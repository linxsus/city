"""État : Appareil Android non connecté"""

from core.etat import Etat


class EtatScrcpyNonConnecte(Etat):
    """État quand aucun appareil Android n'est connecté

    Détection : Aucun appareil n'est détecté via `adb devices`.
    """

    nom = "scrcpy_non_connecte"
    groupes = ["scrcpy", "demarrage"]
    priorite = 0

    def verif(self, manoir) -> bool:
        """Vérifie si aucun appareil n'est connecté

        Args:
            manoir: Instance du manoir (ManoirScrcpy)

        Returns:
            True si aucun appareil Android n'est connecté
        """
        return not manoir.adb.is_device_connected()
