# -*- coding: utf-8 -*-
"""Chemin : Fermer le popup Rapport de développement"""

from typing import List, Any
from core.chemin import Chemin
from core.etat_inconnu import EtatInconnu
from actions.action import ActionSimple
from actions.action_reprise_preparer_tour import ActionReprisePreparerTour


class CheminFermerPopupRapport(Chemin):
    """Chemin pour fermer le popup Rapport de développement

    popup_rapport → inconnu (ville ou autre popup)

    Actions :
    1. Clique en dehors du popup pour le fermer
    2. ActionReprisePreparerTour pour re-détecter l'état après

    Le popup de rapport se ferme en cliquant n'importe où en dehors.
    """
    etat_initial = "popup_rapport"
    # Sortie incertaine : peut être ville ou autre popup
    etat_sortie = EtatInconnu(
        etats_possibles=["ville", "popup_connexion", "popup_gratuit", "chargement"]
    )

    def fonction_actions(self, manoir) -> List[Any]:
        """Génère les actions pour fermer le popup rapport

        Args:
            manoir: Instance du manoir

        Returns:
            Liste d'actions
        """
        # Clic en dehors du popup (coin supérieur gauche)
        def clic_fermer_rapport(m):
            m.click_at(50, 50, relative=True)
            m._ajouter_historique("Fermeture popup rapport")
            return True

        return [
            ActionSimple(
                manoir,
                action_func=clic_fermer_rapport,
                nom="FermerRapportDeveloppement"
            ),
            ActionReprisePreparerTour(manoir),
        ]
