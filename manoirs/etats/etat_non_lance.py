"""État : BlueStacks non lancé"""

from core.etat import Etat


class EtatNonLance(Etat):
    """État quand la fenêtre BlueStacks n'existe pas

    Détection : La fenêtre avec le titre BlueStacks n'est pas trouvée.
    """

    nom = "non_lance"
    groupes = ["demarrage"]

    def verif(self, manoir) -> bool:
        """Vérifie si BlueStacks n'est PAS lancé

        Args:
            manoir: Instance du manoir (pour accéder à find_window)

        Returns:
            True si la fenêtre BlueStacks n'existe pas
        """
        hwnd = manoir.find_window()
        return hwnd is None
