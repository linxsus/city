# -*- coding: utf-8 -*-
"""Chemin : Lancer BlueStacks"""

from typing import List, Any
from core.chemin import Chemin
from actions.bluestacks.action_lancer_raccourci import ActionLancerRaccourci


class CheminLancerBluestacks(Chemin):
    """Chemin pour lancer BlueStacks

    non_lance → chargement

    Actions :
    1. Met le flag _lancement_initie à True
    2. Lance BlueStacks via raccourci
    """
    etat_initial = "non_lance"
    etat_sortie = "chargement"

    def fonction_actions(self, manoir) -> List[Any]:
        """Génère les actions pour lancer BlueStacks

        Args:
            manoir: Instance du manoir

        Returns:
            Liste d'actions
        """
        # Marquer que le lancement est initié par nous
        manoir._lancement_initie = True

        return [
            ActionLancerRaccourci(manoir),
        ]
