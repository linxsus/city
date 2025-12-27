"""État : Ville (jeu prêt)"""

from core.etat import Etat


class EtatVille(Etat):
    """État quand le jeu est chargé et prêt (écran ville)

    Détection :
    - Template ville/icone_jeu_charge.png visible

    Effet de bord :
    - Remet _lancement_initie à False (lancement terminé)
    """

    nom = "ville"
    groupes = ["ecran_principal"]

    def verif(self, manoir) -> bool:
        """Vérifie si le jeu est prêt (icône jeu chargé visible)

        Args:
            manoir: Instance du manoir

        Returns:
            True si le jeu est prêt
        """
        if manoir.detect_image("ville/icone_jeu_charge.png"):
            # Lancement terminé, reset le flag
            manoir._lancement_initie = False
            return True

        return False
