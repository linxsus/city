"""Action pour attendre la connexion d'un appareil Android"""

import time

from actions.action import Action


class ActionAttendreConnexion(Action):
    """Attend qu'un appareil Android soit connecté

    Cette action vérifie périodiquement si un appareil est connecté
    via ADB. Elle demande une rotation pour ne pas bloquer les autres
    manoirs pendant l'attente.
    """

    def __init__(
        self,
        manoir,
        timeout: float = 60.0,
        check_interval: float = 2.0
    ):
        """
        Args:
            manoir: Manoir parent (ManoirScrcpy)
            timeout: Durée maximale d'attente (secondes)
            check_interval: Intervalle entre les vérifications (secondes)
        """
        super().__init__(manoir)
        self.nom = "AttendreConnexion"
        self.timeout = timeout
        self.check_interval = check_interval

        # État interne
        self._start_time = None
        self._last_check = 0

    def condition(self):
        """Exécuter uniquement si aucun appareil n'est connecté"""
        return not self.fenetre.adb.is_device_connected()

    def _run(self):
        """Vérifie la connexion et demande une rotation si nécessaire

        Returns:
            bool: True si appareil connecté, False si timeout ou en attente
        """
        now = time.time()

        # Initialiser le timer au premier appel
        if self._start_time is None:
            self._start_time = now
            self._last_check = now
            self.logger.info(f"Attente de connexion (timeout: {self.timeout}s)...")

        # Vérifier le timeout
        elapsed = now - self._start_time
        if elapsed >= self.timeout:
            self.logger.error(f"Timeout: aucun appareil connecté après {self.timeout}s")
            self._reset()
            return False

        # Vérifier si l'intervalle est écoulé
        if now - self._last_check < self.check_interval:
            # Pas encore le moment de vérifier, demander une rotation
            self.fenetre.demander_rotation()
            return True  # Continuer l'attente

        self._last_check = now

        # Vérifier la connexion
        if self.fenetre.adb.is_device_connected():
            device = self.fenetre.adb.get_device_name() or self.fenetre.adb.device_serial
            self.logger.info(f"Appareil connecté: {device}")
            self._reset()
            return True

        # Toujours en attente
        self.logger.debug(f"En attente... ({elapsed:.0f}/{self.timeout}s)")
        self.fenetre.demander_rotation()
        return True

    def _reset(self):
        """Réinitialise l'état interne"""
        self._start_time = None
        self._last_check = 0

    def __repr__(self):
        return f"ActionAttendreConnexion({self.fenetre.nom}, timeout={self.timeout})"
