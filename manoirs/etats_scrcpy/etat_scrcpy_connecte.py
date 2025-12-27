"""État : Appareil Android connecté (scrcpy non lancé)"""

from core.etat import Etat


class EtatScrcpyConnecte(Etat):
    """État quand l'appareil est connecté mais scrcpy n'est pas lancé

    Détection :
    - Un appareil est détecté via `adb devices`
    - Scrcpy n'est PAS en cours d'exécution
    """

    nom = "scrcpy_connecte"
    groupes = ["scrcpy", "demarrage"]
    priorite = 0

    def verif(self, manoir) -> bool:
        """Vérifie si l'appareil est connecté sans scrcpy

        Args:
            manoir: Instance du manoir (ManoirScrcpy)

        Returns:
            True si appareil connecté ET scrcpy non lancé
        """
        return (
            manoir.adb.is_device_connected()
            and not manoir.is_scrcpy_running()
        )
