"""Gestionnaire de timers avec persistance

Gère les timers pour les tâches récurrentes (collecte, construction, etc.)
Les timers sont persistés en JSON pour survivre aux redémarrages.
"""

import json
import time
from pathlib import Path
from threading import Lock

from utils.config import DATA_DIR, TIMERS_FILE
from utils.logger import get_module_logger

logger = get_module_logger("TimerManager")


class Timer:
    """Représente un timer individuel

    Attributes:
        nom: Nom unique du timer
        fenetre_id: ID de la fenêtre propriétaire (None = global)
        intervalle: Intervalle en secondes entre chaque exécution
        derniere_execution: Timestamp de la dernière exécution
        prochaine_execution: Timestamp de la prochaine exécution prévue
        actif: Si le timer est actif
        priorite: Priorité du timer (plus haut = plus prioritaire)
    """

    def __init__(self, nom, fenetre_id=None, intervalle=3600, priorite=0):
        """
        Args:
            nom: Nom unique du timer
            fenetre_id: ID de la fenêtre (None = timer global)
            intervalle: Intervalle en secondes (défaut: 1 heure)
            priorite: Priorité du timer
        """
        self.nom = nom
        self.fenetre_id = fenetre_id
        self.intervalle = intervalle
        self.derniere_execution = 0
        self.prochaine_execution = 0
        self.actif = True
        self.priorite = priorite

    def is_due(self):
        """Vérifie si le timer est dû

        Returns:
            bool: True si le timer doit être exécuté
        """
        if not self.actif:
            return False
        return time.time() >= self.prochaine_execution

    def time_until_due(self):
        """Retourne le temps restant avant l'échéance

        Returns:
            float: Secondes restantes (négatif si déjà dû)
        """
        return self.prochaine_execution - time.time()

    def mark_executed(self):
        """Marque le timer comme exécuté et calcule la prochaine échéance"""
        self.derniere_execution = time.time()
        self.prochaine_execution = self.derniere_execution + self.intervalle

    def reset(self):
        """Réinitialise le timer (prochaine exécution = maintenant)"""
        self.prochaine_execution = time.time()

    def delay(self, seconds):
        """Retarde le timer

        Args:
            seconds: Nombre de secondes à ajouter
        """
        self.prochaine_execution += seconds

    def to_dict(self):
        """Convertit le timer en dictionnaire pour sérialisation

        Returns:
            dict: Représentation du timer
        """
        return {
            "nom": self.nom,
            "fenetre_id": self.fenetre_id,
            "intervalle": self.intervalle,
            "derniere_execution": self.derniere_execution,
            "prochaine_execution": self.prochaine_execution,
            "actif": self.actif,
            "priorite": self.priorite,
        }

    @classmethod
    def from_dict(cls, data):
        """Crée un timer depuis un dictionnaire

        Args:
            data: Dictionnaire de données

        Returns:
            Timer: Instance de timer
        """
        timer = cls(
            nom=data["nom"],
            fenetre_id=data.get("fenetre_id"),
            intervalle=data.get("intervalle", 3600),
            priorite=data.get("priorite", 0),
        )
        timer.derniere_execution = data.get("derniere_execution", 0)
        timer.prochaine_execution = data.get("prochaine_execution", 0)
        timer.actif = data.get("actif", True)
        return timer

    def __repr__(self):
        status = "DÛ" if self.is_due() else f"dans {self.time_until_due():.0f}s"
        return f"Timer('{self.nom}', fenetre={self.fenetre_id}, {status})"


class TimerManager:
    """Gestionnaire de timers avec persistance

    Gère les timers par fenêtre et les timers globaux.
    Persiste les données en JSON.
    """

    def __init__(self, filepath=None):
        """
        Args:
            filepath: Chemin du fichier de persistance (défaut: config)
        """
        self.filepath = Path(filepath) if filepath else TIMERS_FILE
        self._timers = {}  # {timer_key: Timer}
        self._lock = Lock()

        # Charger les timers existants
        self._load()

    def _get_timer_key(self, nom, fenetre_id=None):
        """Génère la clé unique pour un timer (PROTÉGÉ)"""
        if fenetre_id:
            return f"{fenetre_id}:{nom}"
        return f"global:{nom}"

    def add_timer(self, nom, fenetre_id=None, intervalle=3600, priorite=0, start_now=False):
        """Ajoute un nouveau timer

        Args:
            nom: Nom du timer
            fenetre_id: ID de la fenêtre (None = global)
            intervalle: Intervalle en secondes
            priorite: Priorité du timer
            start_now: Si True, le timer est dû immédiatement

        Returns:
            Timer: Le timer créé
        """
        key = self._get_timer_key(nom, fenetre_id)

        with self._lock:
            if key in self._timers:
                logger.warning(f"Timer '{key}' existe déjà, mise à jour")
                timer = self._timers[key]
                timer.intervalle = intervalle
                timer.priorite = priorite
            else:
                timer = Timer(nom, fenetre_id, intervalle, priorite)
                if start_now:
                    timer.prochaine_execution = time.time()
                else:
                    timer.prochaine_execution = time.time() + intervalle
                self._timers[key] = timer
                logger.debug(f"Timer ajouté: {timer}")

        return timer

    def get_timer(self, nom, fenetre_id=None):
        """Récupère un timer

        Args:
            nom: Nom du timer
            fenetre_id: ID de la fenêtre

        Returns:
            Timer ou None
        """
        key = self._get_timer_key(nom, fenetre_id)
        return self._timers.get(key)

    def remove_timer(self, nom, fenetre_id=None):
        """Supprime un timer

        Args:
            nom: Nom du timer
            fenetre_id: ID de la fenêtre

        Returns:
            bool: True si supprimé
        """
        key = self._get_timer_key(nom, fenetre_id)

        with self._lock:
            if key in self._timers:
                del self._timers[key]
                logger.debug(f"Timer supprimé: {key}")
                return True
        return False

    def get_due_timers(self, fenetre_id=None):
        """Récupère les timers dus pour une fenêtre

        Args:
            fenetre_id: ID de la fenêtre (None = tous)

        Returns:
            List[Timer]: Timers dus, triés par priorité
        """
        due_timers = []

        with self._lock:
            for timer in self._timers.values():
                if timer.is_due() and (
                    fenetre_id is None or timer.fenetre_id == fenetre_id or timer.fenetre_id is None
                ):
                    due_timers.append(timer)

        # Trier par priorité (décroissant)
        due_timers.sort(key=lambda t: t.priorite, reverse=True)

        return due_timers

    def get_fenetre_timers(self, fenetre_id):
        """Récupère tous les timers d'une fenêtre

        Args:
            fenetre_id: ID de la fenêtre

        Returns:
            List[Timer]: Timers de la fenêtre
        """
        timers = []

        with self._lock:
            for timer in self._timers.values():
                if timer.fenetre_id == fenetre_id:
                    timers.append(timer)

        return timers

    def get_global_timers(self):
        """Récupère les timers globaux

        Returns:
            List[Timer]: Timers globaux
        """
        with self._lock:
            return [t for t in self._timers.values() if t.fenetre_id is None]

    def get_next_due_time(self, fenetre_id=None):
        """Récupère le timestamp de la prochaine échéance

        Args:
            fenetre_id: ID de la fenêtre (None = tous)

        Returns:
            float ou None: Timestamp de la prochaine échéance
        """
        next_time = None

        with self._lock:
            for timer in self._timers.values():
                if not timer.actif:
                    continue
                if (
                    fenetre_id is not None
                    and timer.fenetre_id != fenetre_id
                    and timer.fenetre_id is not None
                ):
                    continue
                if next_time is None or timer.prochaine_execution < next_time:
                    next_time = timer.prochaine_execution

        return next_time

    def mark_executed(self, nom, fenetre_id=None):
        """Marque un timer comme exécuté

        Args:
            nom: Nom du timer
            fenetre_id: ID de la fenêtre
        """
        timer = self.get_timer(nom, fenetre_id)
        if timer:
            timer.mark_executed()
            logger.debug(f"Timer exécuté: {timer}")

    def _load(self):
        """Charge les timers depuis le fichier (PROTÉGÉ)"""
        if not self.filepath.exists():
            logger.info("Pas de fichier timers existant, démarrage à vide")
            return

        try:
            with open(self.filepath, encoding="utf-8") as f:
                data = json.load(f)

            with self._lock:
                self._timers = {}
                for timer_data in data.get("timers", []):
                    timer = Timer.from_dict(timer_data)
                    key = self._get_timer_key(timer.nom, timer.fenetre_id)
                    self._timers[key] = timer

            logger.info(f"Chargé {len(self._timers)} timer(s) depuis {self.filepath}")

        except Exception as e:
            logger.error(f"Erreur chargement timers: {e}")

    def save(self):
        """Sauvegarde les timers dans le fichier"""
        try:
            # Créer le dossier si nécessaire
            DATA_DIR.mkdir(parents=True, exist_ok=True)

            with self._lock:
                data = {
                    "last_save": time.time(),
                    "timers": [t.to_dict() for t in self._timers.values()],
                }

            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.debug(f"Sauvegardé {len(self._timers)} timer(s)")

        except Exception as e:
            logger.error(f"Erreur sauvegarde timers: {e}")

    def __len__(self):
        return len(self._timers)

    def __repr__(self):
        return f"TimerManager({len(self._timers)} timers)"


# Instance globale
_timer_manager_instance = None


def get_timer_manager():
    """Retourne une instance singleton de TimerManager

    Returns:
        TimerManager: Instance partagée
    """
    global _timer_manager_instance
    if _timer_manager_instance is None:
        _timer_manager_instance = TimerManager()
    return _timer_manager_instance
