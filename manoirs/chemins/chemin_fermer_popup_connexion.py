# -*- coding: utf-8 -*-
"""Chemin : Collecter la connexion quotidienne"""

from typing import List, Any
from core.chemin import Chemin
from core.etat_inconnu import EtatInconnu
from actions.action import ActionSimple
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
        # Clic sur le popup connexion quotidienne
        def clic_collecter_connexion(m):
            result = m.click_image("popups/connexion_quotidienne.png")
            if result:
                m._ajouter_historique("Connexion quotidienne collectée")
            return result if result else True  # Continue même si clic échoue

        return [
            ActionSimple(
                manoir,
                action_func=clic_collecter_connexion,
                nom="CollecterConnexionQuotidienne"
            ),
            ActionReprisePreparerTour(manoir),
        ]
