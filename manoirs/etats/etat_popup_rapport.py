# -*- coding: utf-8 -*-
"""État : Popup Rapport de développement"""

from core.etat import Etat


class EtatPopupRapport(Etat):
    """État quand le popup Rapport de développement est affiché

    Détection :
    - Template popups/rapport_developpement.png visible

    Priorité haute : les popups doivent être détectés avant les états normaux.
    """
    nom = "popup_rapport"
    groupes = ["popup", "demarrage"]

    def verif(self, manoir) -> bool:
        """Vérifie si le popup rapport est affiché

        Args:
            manoir: Instance du manoir

        Returns:
            True si le popup est visible
        """
        return manoir.detect_image("popups/rapport_developpement.png")
