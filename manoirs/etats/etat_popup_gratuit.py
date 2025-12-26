# -*- coding: utf-8 -*-
"""État : Popup Bouton Gratuit"""

from core.etat import Etat


class EtatPopupGratuit(Etat):
    """État quand un popup avec bouton Gratuit est affiché

    Détection :
    - Template boutons/bouton_gratuit.png visible

    Priorité haute : les popups doivent être détectés avant les états normaux.
    """
    nom = "popup_gratuit"
    groupes = ["popup", "demarrage"]

    def verif(self, manoir) -> bool:
        """Vérifie si un popup avec bouton gratuit est affiché

        Args:
            manoir: Instance du manoir

        Returns:
            True si le bouton gratuit est visible
        """
        return manoir.detect_image("boutons/bouton_gratuit.png")
