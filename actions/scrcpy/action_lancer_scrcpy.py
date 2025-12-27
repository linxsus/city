"""Action pour lancer scrcpy"""

import time

from actions.action import Action


class ActionLancerScrcpy(Action):
    """Lance scrcpy pour afficher l'écran de l'appareil Android

    Cette action lance scrcpy en arrière-plan et attend brièvement
    que la fenêtre apparaisse.
    """

    def __init__(self, manoir, window_title: str = None, wait_time: float = 2.0):
        """
        Args:
            manoir: Manoir parent (ManoirScrcpy)
            window_title: Titre de la fenêtre scrcpy (optionnel)
            wait_time: Temps d'attente après le lancement (secondes)
        """
        super().__init__(manoir)
        self.nom = "LancerScrcpy"
        self.window_title = window_title
        self.wait_time = wait_time

    def condition(self):
        """Exécuter uniquement si l'appareil est connecté et scrcpy non lancé"""
        return (
            self.fenetre.adb.is_device_connected()
            and not self.fenetre.is_scrcpy_running()
        )

    def _run(self):
        """Lance scrcpy

        Returns:
            bool: True si lancé avec succès
        """
        # Vérifier la connexion de l'appareil
        if not self.fenetre.adb.is_device_connected():
            self.logger.error("Aucun appareil connecté")
            return False

        # Si déjà lancé, on passe
        if self.fenetre.is_scrcpy_running():
            self.logger.info("Scrcpy déjà en cours")
            return True

        # Lancer scrcpy
        self.logger.info("Lancement de scrcpy...")
        success = self.fenetre.launch_scrcpy(window_title=self.window_title)

        if success:
            # Attendre que scrcpy démarre
            time.sleep(self.wait_time)
            self.logger.info("Scrcpy lancé avec succès")
            return True
        else:
            self.logger.error("Échec du lancement de scrcpy")
            return False

    def __repr__(self):
        return f"ActionLancerScrcpy({self.fenetre.nom})"
