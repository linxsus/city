# -*- coding: utf-8 -*-
"""État : Popup Connexion quotidienne"""

from core.etat import Etat


class EtatPopupConnexion(Etat):
    """État quand le popup Connexion quotidienne est affiché

    Détection :
    - Template popups/connexion_quotidienne.png visible

    Priorité haute : les popups doivent être détectés avant les états normaux.
    """
    nom = "popup_connexion"
    groupes = ["popup", "demarrage"]

    def verif(self, manoir) -> bool:
        """Vérifie si le popup connexion quotidienne est affiché

        Args:
            manoir: Instance du manoir

        Returns:
            True si le popup est visible
        """
        return manoir.detect_image("popups/connexion_quotidienne.png")
