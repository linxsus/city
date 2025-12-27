"""Gestionnaire d'états des fenêtres avec persistance

Gère les états des fenêtres (actif, exclu, en attente, etc.)
et le compteur de relances.
"""

import json
import time
from enum import Enum
from pathlib import Path
from threading import Lock

from utils.config import DATA_DIR, WINDOW_STATES_FILE
from utils.logger import get_module_logger

logger = get_module_logger("WindowStateManager")


class EtatManoir(Enum):
    """États possibles d'un manoir"""

    ACTIF = "actif"  # Manoir disponible pour rotation
    EXCLU_TEMPORAIRE = "exclu_temp"  # Exclu temporairement (relance en cours)
    EXCLU_2H = "exclu_2h"  # Exclu 2h (compte utilisé ailleurs)
    EN_ATTENTE_LANCEMENT = "attente"  # En attente de lancement
    ERREUR = "erreur"  # En état d'erreur
    DESACTIVE = "desactive"  # Désactivé manuellement


class ManoirState:
    """État d'un manoir individuel

    Attributes:
        manoir_id: ID du manoir
        etat: État actuel (EtatManoir)
        heure_fin_exclusion: Timestamp de fin d'exclusion (si applicable)
        compteur_relances: Nombre de relances consécutives
        derniere_relance: Timestamp de la dernière relance
        derniere_activite: Timestamp de la dernière activité
        message_erreur: Message d'erreur (si applicable)
    """

    def __init__(self, manoir_id):
        """
        Args:
            manoir_id: ID du manoir
        """
        self.manoir_id = manoir_id
        self.etat = EtatManoir.ACTIF
        self.heure_fin_exclusion = 0
        self.compteur_relances = 0
        self.derniere_relance = 0
        self.derniere_activite = 0
        self.message_erreur = None

    def is_available(self):
        """Vérifie si le manoir est disponible pour la rotation

        Returns:
            bool: True si disponible
        """
        # Vérifier si l'exclusion est terminée
        if self.etat in (EtatManoir.EXCLU_TEMPORAIRE, EtatManoir.EXCLU_2H):
            if time.time() >= self.heure_fin_exclusion:
                self.etat = EtatManoir.ACTIF
                self.heure_fin_exclusion = 0
                logger.info(f"Manoir {self.manoir_id}: exclusion terminée")

        return self.etat == EtatManoir.ACTIF

    def time_until_available(self):
        """Retourne le temps restant avant disponibilité

        Returns:
            float: Secondes restantes (0 si déjà disponible)
        """
        if self.is_available():
            return 0

        if self.etat in (EtatManoir.EXCLU_TEMPORAIRE, EtatManoir.EXCLU_2H):
            return max(0, self.heure_fin_exclusion - time.time())

        return float("inf")  # Indisponible indéfiniment

    def set_actif(self):
        """Met le manoir en état actif"""
        self.etat = EtatManoir.ACTIF
        self.heure_fin_exclusion = 0
        self.message_erreur = None
        self.compteur_relances = 0  # Reset après retour à actif

    def set_exclu_temporaire(self, duree_secondes):
        """Exclut temporairement le manoir

        Args:
            duree_secondes: Durée d'exclusion en secondes
        """
        self.etat = EtatManoir.EXCLU_TEMPORAIRE
        self.heure_fin_exclusion = time.time() + duree_secondes
        logger.info(f"Manoir {self.manoir_id}: exclusion temporaire pour {duree_secondes}s")

    def set_exclu_2h(self, message=None):
        """Exclut le manoir pour 2 heures (compte utilisé ailleurs)

        Args:
            message: Message optionnel
        """
        self.etat = EtatManoir.EXCLU_2H
        self.heure_fin_exclusion = time.time() + (2 * 60 * 60)
        self.message_erreur = message or "Compte utilisé ailleurs"
        logger.warning(f"Manoir {self.manoir_id}: exclusion 2h - {self.message_erreur}")

    def set_en_attente(self, message=None):
        """Met le manoir en attente de lancement

        Args:
            message: Message optionnel
        """
        self.etat = EtatManoir.EN_ATTENTE_LANCEMENT
        self.message_erreur = message

    def set_erreur(self, message):
        """Met le manoir en état d'erreur

        Args:
            message: Message d'erreur
        """
        self.etat = EtatManoir.ERREUR
        self.message_erreur = message
        logger.error(f"Manoir {self.manoir_id}: erreur - {message}")

    def set_desactive(self):
        """Désactive le manoir"""
        self.etat = EtatManoir.DESACTIVE

    def incrementer_relance(self):
        """Incrémente le compteur de relances

        Returns:
            int: Nouveau compteur de relances
        """
        self.compteur_relances += 1
        self.derniere_relance = time.time()

        if self.compteur_relances >= 2:
            logger.warning(
                f"Manoir {self.manoir_id}: {self.compteur_relances} relances "
                "consécutives - problème récurrent possible"
            )

        return self.compteur_relances

    def reset_relances(self):
        """Réinitialise le compteur de relances"""
        self.compteur_relances = 0

    def marquer_activite(self):
        """Marque une activité sur le manoir"""
        self.derniere_activite = time.time()

    def to_dict(self):
        """Convertit en dictionnaire pour sérialisation"""
        return {
            "manoir_id": self.manoir_id,
            "etat": self.etat.value,
            "heure_fin_exclusion": self.heure_fin_exclusion,
            "compteur_relances": self.compteur_relances,
            "derniere_relance": self.derniere_relance,
            "derniere_activite": self.derniere_activite,
            "message_erreur": self.message_erreur,
        }

    @classmethod
    def from_dict(cls, data):
        """Crée un état depuis un dictionnaire"""
        state = cls(data["manoir_id"])
        state.etat = EtatManoir(data.get("etat", "actif"))
        state.heure_fin_exclusion = data.get("heure_fin_exclusion", 0)
        state.compteur_relances = data.get("compteur_relances", 0)
        state.derniere_relance = data.get("derniere_relance", 0)
        state.derniere_activite = data.get("derniere_activite", 0)
        state.message_erreur = data.get("message_erreur")
        return state

    def __repr__(self):
        if self.etat in (EtatManoir.EXCLU_TEMPORAIRE, EtatManoir.EXCLU_2H):
            remaining = self.time_until_available()
            return f"ManoirState({self.manoir_id}, {self.etat.value}, {remaining:.0f}s)"
        return f"ManoirState({self.manoir_id}, {self.etat.value})"


class ManoirStateManager:
    """Gestionnaire d'états des manoirs avec persistance"""

    def __init__(self, filepath=None):
        """
        Args:
            filepath: Chemin du fichier de persistance
        """
        self.filepath = Path(filepath) if filepath else WINDOW_STATES_FILE
        self._states = {}  # {manoir_id: ManoirState}
        self._lock = Lock()

        # Charger les données existantes
        self._load()

    def register_manoir(self, manoir_id):
        """Enregistre un manoir

        Args:
            manoir_id: ID du manoir

        Returns:
            ManoirState: État du manoir
        """
        with self._lock:
            if manoir_id not in self._states:
                self._states[manoir_id] = ManoirState(manoir_id)
                logger.debug(f"Manoir {manoir_id} enregistré")
            return self._states[manoir_id]

    def get_state(self, manoir_id):
        """Récupère l'état d'un manoir

        Args:
            manoir_id: ID du manoir

        Returns:
            ManoirState ou None
        """
        return self._states.get(manoir_id)

    def is_available(self, manoir_id):
        """Vérifie si un manoir est disponible

        Args:
            manoir_id: ID du manoir

        Returns:
            bool: True si disponible
        """
        state = self.get_state(manoir_id)
        if state:
            return state.is_available()
        return False

    def get_available_manoirs(self):
        """Récupère les IDs des manoirs disponibles

        Returns:
            List[str]: IDs des manoirs disponibles
        """
        with self._lock:
            return [mid for mid, state in self._states.items() if state.is_available()]

    def get_all_states(self):
        """Récupère tous les états

        Returns:
            Dict[str, ManoirState]: Dictionnaire des états
        """
        with self._lock:
            return self._states.copy()

    def set_actif(self, manoir_id):
        """Met un manoir en état actif"""
        state = self.get_state(manoir_id)
        if state:
            state.set_actif()

    def set_exclu_temporaire(self, manoir_id, duree_secondes):
        """Exclut temporairement un manoir"""
        state = self.get_state(manoir_id)
        if state:
            state.set_exclu_temporaire(duree_secondes)

    def set_exclu_2h(self, manoir_id, message=None):
        """Exclut un manoir pour 2h"""
        state = self.get_state(manoir_id)
        if state:
            state.set_exclu_2h(message)

    def set_erreur(self, manoir_id, message):
        """Met un manoir en état d'erreur"""
        state = self.get_state(manoir_id)
        if state:
            state.set_erreur(message)

    def incrementer_relance(self, manoir_id):
        """Incrémente le compteur de relances

        Returns:
            int: Nouveau compteur
        """
        state = self.get_state(manoir_id)
        if state:
            return state.incrementer_relance()
        return 0

    def marquer_activite(self, manoir_id):
        """Marque une activité sur un manoir"""
        state = self.get_state(manoir_id)
        if state:
            state.marquer_activite()

    def _load(self):
        """Charge les données depuis le fichier (PROTÉGÉ)"""
        if not self.filepath.exists():
            logger.info("Pas de fichier états existant, démarrage à vide")
            return

        try:
            with open(self.filepath, encoding="utf-8") as f:
                data = json.load(f)

            with self._lock:
                self._states = {}
                for state_data in data.get("states", []):
                    state = ManoirState.from_dict(state_data)
                    self._states[state.manoir_id] = state

            logger.info(f"Chargé {len(self._states)} état(s) de manoir")

        except Exception as e:
            logger.error(f"Erreur chargement états: {e}")

    def save(self):
        """Sauvegarde les données dans le fichier"""
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)

            with self._lock:
                data = {
                    "last_save": time.time(),
                    "states": [s.to_dict() for s in self._states.values()],
                }

            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.debug("États sauvegardés")

        except Exception as e:
            logger.error(f"Erreur sauvegarde états: {e}")

    def __len__(self):
        return len(self._states)

    def __repr__(self):
        available = len(self.get_available_manoirs())
        return f"ManoirStateManager({len(self._states)} manoirs, {available} disponibles)"


# Instance globale
_manoir_state_manager_instance = None


def get_manoir_state_manager():
    """Retourne une instance singleton de ManoirStateManager

    Returns:
        ManoirStateManager: Instance partagée
    """
    global _manoir_state_manager_instance
    if _manoir_state_manager_instance is None:
        _manoir_state_manager_instance = ManoirStateManager()
    return _manoir_state_manager_instance


# Alias pour compatibilité avec l'ancien nom
get_window_state_manager = get_manoir_state_manager
