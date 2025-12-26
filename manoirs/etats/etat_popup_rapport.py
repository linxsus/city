# -*- coding: utf-8 -*-
"""État : Popup Rapport de développement"""

from core.popup import Popup


class EtatPopupRapport(Popup):
    """État quand le popup Rapport de développement est affiché

    Détection :
    - Template popups/rapport_developpement.png visible

    Fermeture :
    - Clic en dehors du popup (coin supérieur gauche)

    Priorité haute : les popups doivent être détectés avant les états normaux.
    """
    nom = "popup_rapport"
    groupes = ["popup", "demarrage"]
    image_detection = "popups/rapport_developpement.png"
    position_fermeture = (50, 50)
    position_relative = True
    etats_possibles_apres = ["ville", "popup_connexion", "popup_gratuit", "chargement"]
