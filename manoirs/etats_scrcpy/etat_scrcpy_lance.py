"""État : Scrcpy lancé et prêt"""

from core.etat import Etat


class EtatScrcpyLance(Etat):
    """État quand scrcpy est lancé et l'appareil est prêt

    Détection :
    - Un appareil est connecté
    - Scrcpy est en cours d'exécution
    """

    nom = "scrcpy_lance"
    groupes = ["scrcpy", "pret"]
    priorite = 0

    def verif(self, manoir) -> bool:
        """Vérifie si scrcpy est lancé

        Args:
            manoir: Instance du manoir (ManoirScrcpy)

        Returns:
            True si appareil connecté ET scrcpy lancé
        """
        return (
            manoir.adb.is_device_connected()
            and manoir.is_scrcpy_running()
        )
