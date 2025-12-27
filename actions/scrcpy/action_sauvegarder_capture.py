"""Action pour sauvegarder une capture d'écran"""

from pathlib import Path
from typing import Optional

from actions.action import Action


class ActionSauvegarderCapture(Action):
    """Sauvegarde une capture d'écran de l'appareil Android

    Peut sauvegarder l'écran complet ou une région spécifique.
    Utile pour créer des templates pour le générateur.
    """

    def __init__(
        self,
        manoir,
        template_name: Optional[str] = None,
        region: Optional[tuple] = None,
        suffix: str = ""
    ):
        """
        Args:
            manoir: Manoir parent (ManoirScrcpy)
            template_name: Nom pour sauvegarder comme template (dans templates/scrcpy/)
                          Si None, sauvegarde dans captures/ avec timestamp
            region: Région à capturer (x, y, w, h) ou None pour tout l'écran
            suffix: Suffixe pour le nom de fichier (si pas de template_name)
        """
        super().__init__(manoir)
        self.nom = "SauvegarderCapture"
        self.template_name = template_name
        self.region = region
        self.suffix = suffix

    def condition(self):
        """Exécuter uniquement si l'appareil est connecté"""
        return self.fenetre.adb.is_device_connected()

    def _run(self):
        """Sauvegarde la capture

        Returns:
            bool: True si sauvegardé avec succès
        """
        if self.template_name:
            # Sauvegarder comme template
            filepath = self.fenetre.save_capture_for_template(
                self.template_name,
                region=self.region
            )
        else:
            # Sauvegarder dans captures/
            filepath = self.fenetre.save_capture(suffix=self.suffix)

        if filepath:
            self.logger.info(f"Capture sauvegardée: {filepath}")
            return True
        else:
            self.logger.error("Échec de la sauvegarde de la capture")
            return False

    def __repr__(self):
        if self.template_name:
            return f"ActionSauvegarderCapture(template={self.template_name})"
        return f"ActionSauvegarderCapture(suffix={self.suffix})"
