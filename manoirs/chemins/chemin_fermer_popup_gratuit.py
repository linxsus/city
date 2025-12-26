# -*- coding: utf-8 -*-
"""Chemin : Cliquer sur le bouton Gratuit"""

from typing import List, Any
from core.chemin import Chemin
from core.etat_inconnu import EtatInconnu
from actions.action import ActionSimple
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
        # Clic sur le bouton gratuit
        def clic_bouton_gratuit(m):
            result = m.click_image("boutons/bouton_gratuit.png")
            if result:
                m._ajouter_historique("Bouton gratuit cliqué")
            return result if result else True  # Continue même si clic échoue

        return [
            ActionSimple(
                manoir,
                action_func=clic_bouton_gratuit,
                nom="ClicBoutonGratuit"
            ),
            ActionReprisePreparerTour(manoir),
        ]
