"""Détection de l'activité utilisateur (souris + clavier)

Utilise pynput pour une détection non-bloquante.
Fonctionne sur Windows, macOS et Linux.
"""

import time
from threading import Lock

from utils.config import ACTIVITY_CHECK_INTERVAL, PAUSE_SI_ACTIVITE_USER
from utils.logger import get_module_logger

logger = get_module_logger("UserActivityDetector")

# Import conditionnel
try:
    from pynput import keyboard, mouse

    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False
    logger.warning("pynput non disponible - Détection activité désactivée")


class UserActivityDetector:
    """Détecteur d'activité utilisateur (souris + clavier)

    Surveille les mouvements de souris, clics et frappes clavier
    pour détecter si l'utilisateur est actif.
    """

    def __init__(self):
        """Initialise le détecteur"""
        self._derniere_activite = 0
        self._lock = Lock()
        self._running = False
        self._mouse_listener = None
        self._keyboard_listener = None

        # Position souris pour détecter mouvements
        self._last_mouse_pos = None

    def start(self):
        """Démarre la détection

        Returns:
            bool: True si démarré avec succès
        """
        if not PYNPUT_AVAILABLE:
            logger.warning("pynput non disponible - Détection désactivée")
            return False

        if self._running:
            logger.warning("Détecteur déjà en cours d'exécution")
            return True

        logger.info("Démarrage de la détection d'activité utilisateur")
        self._running = True

        try:
            # Listener souris
            self._mouse_listener = mouse.Listener(
                on_move=self._on_mouse_move,
                on_click=self._on_mouse_click,
                on_scroll=self._on_mouse_scroll,
            )
            self._mouse_listener.start()

            # Listener clavier
            self._keyboard_listener = keyboard.Listener(on_press=self._on_key_press)
            self._keyboard_listener.start()

            # Initialiser le timestamp
            self._derniere_activite = time.time()

            logger.info("Détection d'activité démarrée")
            return True

        except Exception as e:
            logger.error(f"Erreur démarrage détection: {e}")
            self._running = False
            return False

    def stop(self):
        """Arrête la détection"""
        if not self._running:
            return

        logger.info("Arrêt de la détection d'activité")
        self._running = False

        try:
            if self._mouse_listener:
                self._mouse_listener.stop()
                self._mouse_listener = None

            if self._keyboard_listener:
                self._keyboard_listener.stop()
                self._keyboard_listener = None

        except Exception as e:
            logger.error(f"Erreur arrêt détection: {e}")

        logger.info("Détection d'activité arrêtée")

    def _on_mouse_move(self, x, y):
        """Callback mouvement souris (PROTÉGÉ)"""
        with self._lock:
            self._derniere_activite = time.time()
            self._last_mouse_pos = (x, y)

    def _on_mouse_click(self, x, y, button, pressed):
        """Callback clic souris (PROTÉGÉ)"""
        if pressed:
            with self._lock:
                self._derniere_activite = time.time()

    def _on_mouse_scroll(self, x, y, dx, dy):
        """Callback scroll souris (PROTÉGÉ)"""
        with self._lock:
            self._derniere_activite = time.time()

    def _on_key_press(self, key):
        """Callback touche clavier (PROTÉGÉ)"""
        with self._lock:
            self._derniere_activite = time.time()

    def is_user_active(self, timeout=2.0):
        """Vérifie si l'utilisateur a été actif récemment

        Args:
            timeout: Secondes depuis la dernière activité

        Returns:
            bool: True si activité détectée dans le timeout
        """
        if not PYNPUT_AVAILABLE or not self._running:
            return False

        with self._lock:
            elapsed = time.time() - self._derniere_activite
            return elapsed < timeout

    def get_time_since_activity(self):
        """Retourne le temps écoulé depuis la dernière activité

        Returns:
            float: Secondes depuis la dernière activité
        """
        with self._lock:
            return time.time() - self._derniere_activite

    def wait_for_inactivity(self, inactivity_duration=2.0, max_wait=None):
        """Attend que l'utilisateur soit inactif

        Args:
            inactivity_duration: Durée d'inactivité requise (secondes)
            max_wait: Attente maximale (secondes), None = PAUSE_SI_ACTIVITE_USER

        Returns:
            bool: True si inactivité atteinte, False si timeout
        """
        if max_wait is None:
            max_wait = PAUSE_SI_ACTIVITE_USER

        start = time.time()

        while (time.time() - start) < max_wait:
            if not self.is_user_active(inactivity_duration):
                logger.debug(f"Inactivité détectée après {time.time() - start:.1f}s")
                return True
            time.sleep(ACTIVITY_CHECK_INTERVAL)

        logger.warning(f"Timeout d'attente d'inactivité ({max_wait}s)")
        return False

    def reset_activity_timer(self):
        """Réinitialise le timer d'activité

        Utile après une action automatique pour éviter de la confondre
        avec une activité utilisateur.
        """
        with self._lock:
            self._derniere_activite = time.time()

    def get_last_mouse_position(self):
        """Retourne la dernière position de souris détectée

        Returns:
            Tuple (x, y) ou None
        """
        with self._lock:
            return self._last_mouse_pos

    @property
    def is_running(self):
        """Vérifie si le détecteur est en cours d'exécution"""
        return self._running


# Instance globale
_activity_detector_instance = None


def get_activity_detector():
    """Retourne une instance singleton de UserActivityDetector

    Returns:
        UserActivityDetector: Instance partagée
    """
    global _activity_detector_instance
    if _activity_detector_instance is None:
        _activity_detector_instance = UserActivityDetector()
    return _activity_detector_instance
