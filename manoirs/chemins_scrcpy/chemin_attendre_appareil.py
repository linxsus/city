"""Chemin : Attendre la connexion d'un appareil"""

from typing import Any

from actions.scrcpy.action_attendre_connexion import ActionAttendreConnexion
from core.chemin import Chemin


class CheminAttendreAppareil(Chemin):
    """Chemin pour attendre qu'un appareil soit connecté

    scrcpy_non_connecte → scrcpy_connecte

    Actions :
    1. Attend qu'un appareil soit détecté via ADB (non-bloquant)
    """

    etat_initial = "scrcpy_non_connecte"
    etat_sortie = "scrcpy_connecte"

    def fonction_actions(self, manoir) -> list[Any]:
        """Génère les actions pour attendre la connexion

        Args:
            manoir: Instance du manoir (ManoirScrcpy)

        Returns:
            Liste d'actions
        """
        return [
            ActionAttendreConnexion(manoir, timeout=300),  # 5 minutes max
        ]
