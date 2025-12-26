# -*- coding: utf-8 -*-
"""Chemin : Collecter la connexion quotidienne"""

from typing import List, Any
from core.chemin import Chemin
from core.etat_inconnu import EtatInconnu
from actions.simple.action_bouton import ActionBouton
from actions.action_reprise_preparer_tour import ActionReprisePreparerTour


class CheminFermerPopupConnexion(Chemin):
    """Chemin pour collecter la connexion quotidienne

    popup_connexion → inconnu (ville ou autre popup)

    Actions :
    1. Clique sur le popup de connexion quotidienne pour collecter
    2. ActionReprisePreparerTour pour re-détecter l'état après

    Le popup de connexion quotidienne se ferme en cliquant dessus.
    """
    etat_initial = "popup_connexion"
    # Sortie incertaine : peut être ville ou autre popup
    etat_sortie = EtatInconnu(
        etats_possibles=["ville", "popup_rapport", "popup_gratuit", "chargement"]
    )

    def fonction_actions(self, manoir) -> List[Any]:
        """Génère les actions pour collecter la connexion quotidienne

        Args:
            manoir: Instance du manoir

        Returns:
            Liste d'actions
        """
        return [
            ActionBouton(manoir, "popups/connexion_quotidienne.png"),
            ActionReprisePreparerTour(manoir),
        ]
