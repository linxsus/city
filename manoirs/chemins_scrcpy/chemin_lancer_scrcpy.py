"""Chemin : Lancer scrcpy"""

from typing import Any

from actions.scrcpy.action_lancer_scrcpy import ActionLancerScrcpy
from actions.simple.action_attendre import ActionAttendre
from core.chemin import Chemin


class CheminLancerScrcpy(Chemin):
    """Chemin pour lancer scrcpy

    scrcpy_connecte → scrcpy_lance

    Actions :
    1. Lance scrcpy via la commande système
    2. Attend quelques secondes que scrcpy démarre
    """

    etat_initial = "scrcpy_connecte"
    etat_sortie = "scrcpy_lance"

    def fonction_actions(self, manoir) -> list[Any]:
        """Génère les actions pour lancer scrcpy

        Args:
            manoir: Instance du manoir (ManoirScrcpy)

        Returns:
            Liste d'actions
        """
        return [
            ActionLancerScrcpy(manoir),
            ActionAttendre(manoir, 3),  # Attendre que scrcpy soit prêt
        ]
