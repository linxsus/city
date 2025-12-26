# -*- coding: utf-8 -*-
"""Chemin : Cliquer sur le bouton Gratuit"""

from typing import List, Any
from core.chemin import Chemin
from core.etat_inconnu import EtatInconnu
from actions.simple.action_bouton import ActionBouton
from actions.action_reprise_preparer_tour import ActionReprisePreparerTour


class CheminFermerPopupGratuit(Chemin):
    """Chemin pour cliquer sur le bouton Gratuit

    popup_gratuit → inconnu (ville ou autre popup)

    Actions :
    1. Clique sur le bouton Gratuit
    2. ActionReprisePreparerTour pour re-détecter l'état après

    Ce popup offre quelque chose de gratuit. On clique pour récupérer.
    """
    etat_initial = "popup_gratuit"
    # Sortie incertaine : peut être ville ou autre popup
    etat_sortie = EtatInconnu(
        etats_possibles=["ville", "popup_rapport", "popup_connexion", "chargement"]
    )

    def fonction_actions(self, manoir) -> List[Any]:
        """Génère les actions pour cliquer sur bouton gratuit

        Args:
            manoir: Instance du manoir

        Returns:
            Liste d'actions
        """
        return [
            ActionBouton(manoir, "boutons/bouton_gratuit.png"),
            ActionReprisePreparerTour(manoir),
        ]
