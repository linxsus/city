"""Manoir BlueStacks - Classe abstraite pour gérer une fenêtre BlueStacks

ManoirBlueStacks gère le cycle de vie d'une fenêtre BlueStacks via le
système états/chemins :
- États : non_lance, chargement, popup_*, ville
- Chemins : navigations automatiques entre états

Navigation :
    non_lance → chargement (via chemin_lancer_bluestacks)
    chargement → ville/popups (via chemin_attendre_chargement)
    popup_* → ville (via chemin_fermer_popup_*)
    ville = état final (jeu prêt)

Les sous-classes doivent implémenter gestion_tour() pour la logique métier.
"""

import time
from abc import abstractmethod
from enum import Enum, auto

from manoirs.config_manoirs import HAUTEUR_DEFAUT, LARGEUR_DEFAUT, get_config
from manoirs.manoir_base import ManoirBase


class EtatBlueStacks(Enum):
    """États internes du manoir BlueStacks

    Note: La navigation utilise le système états/chemins.
    Cet enum gère uniquement l'état de blocage.
    """

    EN_COURS = auto()  # Navigation en cours (pas encore en ville)
    PRET = auto()  # Jeu chargé (état "ville"), prêt à automatiser
    BLOQUE = auto()  # Trop d'échecs, reboot nécessaire


class ManoirBlueStacks(ManoirBase):
    """Manoir BlueStacks - Gère une instance BlueStacks

    Classe abstraite qui gère le cycle de vie d'une fenêtre BlueStacks
    via le système états/chemins.

    États écran (via gestionnaire) :
    - non_lance : BlueStacks pas lancé
    - chargement : En cours de chargement
    - popup_rapport, popup_connexion, popup_gratuit : Popups de démarrage
    - ville : Jeu chargé et prêt

    État interne :
    - EN_COURS : Navigation vers "ville" en cours
    - PRET : État "ville" atteint
    - BLOQUE : Timeout ou erreur, reboot au prochain tour

    Timeout:
    - 30 minutes pour atteindre l'état "ville"
    - En cas de timeout: sauvegarde écran + log détaillé
    """

    # Timeout de lancement en secondes (30 minutes)
    TIMEOUT_LANCEMENT = 30 * 60

    # État destination
    ETAT_DESTINATION = "ville"

    def __init__(self, manoir_id="bluestacks", config=None):
        """
        Args:
            manoir_id: Identifiant unique
            config: Configuration (dict) ou None pour charger depuis config_manoirs
        """
        if config is None:
            config = get_config(manoir_id) or {}

        super().__init__(
            manoir_id=manoir_id,
            nom=config.get("nom", "Manoir BlueStacks"),
            titre_bluestacks=config.get("titre_bluestacks", "BlueStacks App Player"),
            largeur=config.get("largeur", LARGEUR_DEFAUT),
            hauteur=config.get("hauteur", HAUTEUR_DEFAUT),
            priorite=config.get("priorite", 50),
            slots_config=config.get("slots_config"),
            position_x=config.get("position_x"),
            position_y=config.get("position_y"),
        )

        # Configuration spécifique
        self.commande_lancement = config.get("commande_lancement", [])
        self.temps_initialisation = config.get("temps_initialisation", 60)

        # État interne (pour timeout et blocage)
        self._etat_interne = EtatBlueStacks.EN_COURS
        self._heure_lancement = None  # Timestamp du début de navigation

        # Flag pour le lancement (utilisé par les états chargement/ville)
        self._lancement_initie = False

        # Historique des actions pour le debug
        self._historique_actions = []

    @property
    def etat(self):
        """État interne du manoir (EN_COURS, PRET, BLOQUE)"""
        return self._etat_interne

    @etat.setter
    def etat(self, nouvel_etat):
        """Change l'état interne avec log"""
        if nouvel_etat != self._etat_interne:
            self.logger.info(f"{self.nom}: {self._etat_interne.name} -> {nouvel_etat.name}")
            self._ajouter_historique(
                f"État interne: {self._etat_interne.name} -> {nouvel_etat.name}"
            )
            self._etat_interne = nouvel_etat

    # =========================================================
    # HISTORIQUE DES ACTIONS (pour debug)
    # =========================================================

    def _ajouter_historique(self, message):
        """Ajoute un message à l'historique des actions

        Args:
            message: Message à ajouter
        """
        timestamp = time.strftime("%H:%M:%S")
        self._historique_actions.append(f"[{timestamp}] {message}")

        # Limiter la taille de l'historique
        if len(self._historique_actions) > 100:
            self._historique_actions = self._historique_actions[-100:]

    def get_historique_actions(self):
        """Retourne l'historique des actions

        Returns:
            list: Liste des messages d'historique
        """
        return self._historique_actions.copy()

    # =========================================================
    # SURCHARGE - Gestion propre des erreurs pendant le démarrage
    # =========================================================

    def capture(self, force=False):
        """Capture l'écran - silencieux si manoir bloqué"""
        if self._etat_interne == EtatBlueStacks.BLOQUE:
            return None
        return super().capture(force)

    def detect_image(self, template_path, threshold=None, region=None):
        """Détecte une image - silencieux si manoir bloqué"""
        if self._etat_interne == EtatBlueStacks.BLOQUE:
            return False
        return super().detect_image(template_path, threshold, region)

    def find_image(self, template_path, threshold=None, region=None):
        """Trouve une image - silencieux si manoir bloqué"""
        if self._etat_interne == EtatBlueStacks.BLOQUE:
            return None
        return super().find_image(template_path, threshold, region)

    # =========================================================
    # LANCEMENT ET REBOOT
    # =========================================================

    def est_fenetre_ouverte(self):
        """Vérifie si la fenêtre BlueStacks est ouverte"""
        hwnd = self.find_window()
        return hwnd is not None

    def _reboot_bluestacks(self):
        """Reboot BlueStacks après un blocage

        Ferme la fenêtre BlueStacks si elle existe, puis reset tous les flags
        et la séquence pour relancer la navigation depuis l'état non_lance.
        """
        self.logger.warning(f"{self.nom}: Reboot en cours...")
        self._ajouter_historique("REBOOT: Réinitialisation complète")

        # Fermer la fenêtre BlueStacks si elle existe
        if self._hwnd:
            self.logger.info(f"Fermeture de la fenêtre BlueStacks (hwnd={self._hwnd})")
            self._wm.close_window(self._hwnd)
            # Attendre un peu que la fenêtre se ferme
            time.sleep(2)

        # Reset des flags
        self._heure_lancement = None
        self._hwnd = None
        self._rect = None
        self._lancement_initie = False
        self.etat_actuel = None  # Force re-détection

        # Vider la séquence et l'historique
        self.sequence.clear()
        self._historique_actions.clear()

        # Repasser en EN_COURS pour relancer
        self.etat = EtatBlueStacks.EN_COURS

    # =========================================================
    # GESTION DU TIMEOUT
    # =========================================================

    def get_temps_depuis_lancement(self):
        """Retourne le temps écoulé depuis le début de la navigation

        Returns:
            float: Temps en secondes, ou 0 si pas commencé
        """
        if self._heure_lancement is None:
            return 0
        return time.time() - self._heure_lancement

    def est_timeout_atteint(self):
        """Vérifie si le timeout est atteint

        Returns:
            bool: True si timeout atteint
        """
        return self.get_temps_depuis_lancement() >= self.TIMEOUT_LANCEMENT

    def est_jeu_pret(self):
        """Vérifie si le jeu est prêt (état PRET)

        Returns:
            bool: True si état PRET
        """
        return self._etat_interne == EtatBlueStacks.PRET

    def sauvegarder_etat_timeout(self):
        """Sauvegarde l'état complet lors d'un timeout

        Sauvegarde:
        - Screenshot de l'écran
        - Log de l'historique des actions

        Returns:
            Path: Chemin du screenshot sauvegardé
        """
        self.logger.error(f"{self.nom}: TIMEOUT après {self.TIMEOUT_LANCEMENT // 60} minutes")

        # Sauvegarder le screenshot
        screenshot_path = self.save_capture(suffix="_TIMEOUT")

        # Logger l'historique des actions
        self.logger.error("=== HISTORIQUE DES ACTIONS ===")
        for ligne in self._historique_actions:
            self.logger.error(ligne)
        self.logger.error("=== FIN HISTORIQUE ===")

        # Logger l'état actuel
        etat_nom = self.etat_actuel.nom if self.etat_actuel else "inconnu"
        self.logger.error(f"État écran: {etat_nom}")
        self.logger.error(f"État interne: {self._etat_interne.name}")
        self.logger.error(f"Temps depuis lancement: {self.get_temps_depuis_lancement():.1f}s")
        self.logger.error(f"Séquence: {self.sequence}")

        return screenshot_path

    # =========================================================
    # IMPLÉMENTATION - Hooks et gestion erreurs
    # =========================================================

    def _hook_reprise_changement(self):
        """Active la fenêtre et vérifie les dimensions lors de la reprise

        Appelé par ManoirBase._preparer_reprise_changement() quand
        Engine revient sur ce manoir après en avoir traité un autre.
        """
        self.activate()  # Active fenêtre + vérifie/replace dimensions

    def _detecter_erreur(self):
        """Détecte si le manoir est en état d'erreur (BLOQUE)

        Returns:
            bool: True si état BLOQUE
        """
        return self._etat_interne == EtatBlueStacks.BLOQUE

    def _gerer_erreur(self):
        """Gère l'état d'erreur - lance le reboot

        Returns:
            bool: False (manoir pas prêt)
        """
        self._reboot_bluestacks()
        return False

    def _preparer_alimenter_sequence(self):
        """Alimente la séquence via le système états/chemins

        Logique :
        1. Vérifier l'état actuel
        2. Si état "ville" → PRET, appeler gestion_tour()
        3. Sinon → Naviguer vers "ville"
        4. Vérifier le timeout

        Returns:
            bool: True si prêt à exécuter, False sinon
        """
        # ===== Vérifier l'état écran actuel =====
        if not self.verifier_etat():
            # Impossible de déterminer l'état (pas de gestionnaire, etc.)
            self.logger.warning("Impossible de déterminer l'état actuel")
            return False

        etat_nom = self.etat_actuel.nom if self.etat_actuel else "inconnu"
        self._ajouter_historique(f"État détecté: {etat_nom}")

        # ===== ÉTAT ÉCRAN: ville → PRET =====
        if etat_nom == self.ETAT_DESTINATION:
            if self._etat_interne != EtatBlueStacks.PRET:
                self._ajouter_historique("Destination atteinte - passage en PRET")
                self.etat = EtatBlueStacks.PRET
                self._heure_lancement = None  # Reset le timer
                self.logger.info(f"{self.nom}: Jeu chargé et prêt !")

            self.activate()
            self.gestion_tour()
            return True

        # ===== Pas encore en "ville" → Navigation =====
        # Démarrer le timer si pas encore fait
        if self._heure_lancement is None:
            self._heure_lancement = time.time()
            self._ajouter_historique("Navigation vers ville initiée")
            self.logger.info(f"{self.nom}: Navigation vers {self.ETAT_DESTINATION}...")

        # Vérifier le timeout
        if self.est_timeout_atteint():
            self._ajouter_historique(f"TIMEOUT: {self.TIMEOUT_LANCEMENT // 60} minutes écoulées")
            self.sauvegarder_etat_timeout()
            self.etat = EtatBlueStacks.BLOQUE
            return False

        # Naviguer vers la destination
        self.naviguer_vers(self.ETAT_DESTINATION)
        return True

    def signaler_blocage(self):
        """Appelé par Engine quand trop d'échecs consécutifs"""
        self.logger.warning(f"{self.nom}: Blocage détecté, reboot prévu au prochain tour")
        self._ajouter_historique("BLOCAGE signalé par Engine")
        self._stats["erreurs_detectees"] += 1
        self.etat = EtatBlueStacks.BLOQUE

    # =========================================================
    # MÉTHODE ABSTRAITE - À implémenter par les sous-classes
    # =========================================================

    @abstractmethod
    def gestion_tour(self):
        """Logique métier du manoir - À implémenter

        Appelée quand le jeu est PRET (état "ville").
        Doit alimenter la séquence avec les actions à exécuter.
        """
        pass

    def definir_timers(self):
        """Définit les timers - vide par défaut, à surcharger"""
        pass

    def initialiser_sequence(self):
        """Initialise la séquence - vide car gérée par preparer_tour()"""
        pass

    def reset(self):
        """Reset le manoir - surcharge pour reset du flag lancement"""
        super().reset()
        self._lancement_initie = False
        self._heure_lancement = None

    # =========================================================
    # INFORMATIONS
    # =========================================================

    def get_status(self):
        """Retourne le statut du manoir"""
        etat_ecran = self.etat_actuel.nom if self.etat_actuel else "inconnu"
        status = {
            "manoir_id": self.manoir_id,
            "nom": self.nom,
            "etat_interne": self._etat_interne.name,
            "etat_ecran": etat_ecran,
            "fenetre_ouverte": self.est_fenetre_ouverte(),
            "jeu_charge": self._etat_interne == EtatBlueStacks.PRET,
            "temps_lancement": self.get_temps_depuis_lancement(),
            "titre": self.titre_bluestacks,
        }
        status.update(self._stats)
        return status

    def __repr__(self):
        etat_ecran = self.etat_actuel.nom if self.etat_actuel else "?"
        return (
            f"ManoirBlueStacks('{self.manoir_id}', {self._etat_interne.name}, écran={etat_ecran})"
        )
