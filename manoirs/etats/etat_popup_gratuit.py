# -*- coding: utf-8 -*-
"""État : Popup Bouton Gratuit"""

from core.popup import Popup


class EtatPopupGratuit(Popup):
    """État quand un popup avec bouton Gratuit est affiché

    Détection :
    - Template boutons/bouton_gratuit.png visible

    Fermeture :
    - Clic sur le bouton gratuit (même image)

    Priorité haute : les popups doivent être détectés avant les états normaux.
    Note: États de sortie définis par groupe "ville" dans config/etat-chemin.toml
    """
    nom = "popup_gratuit"
    groupes = ["popup", "demarrage"]
    image_detection = "boutons/bouton_gratuit.png"
    etats_possibles_extra = ["chargement"]
