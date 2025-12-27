"""Chemin : Lancer BlueStacks"""

from typing import Any

from actions.bluestacks.action_lancer_raccourci import ActionLancerRaccourci
from actions.simple.action_attendre import ActionAttendre
from core.chemin import Chemin


class CheminLancerBluestacks(Chemin):
    """Chemin pour lancer BlueStacks

    non_lance → chargement

    Actions :
    1. Met le flag _lancement_initie à True
    2. Lance BlueStacks via raccourci
    3. Attend temps_initialisation (300s) de façon non-bloquante
    """

    etat_initial = "non_lance"
    etat_sortie = "chargement"

    def fonction_actions(self, manoir) -> list[Any]:
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
            ActionAttendre(manoir, manoir.temps_initialisation),
        ]
