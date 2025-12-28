"""
Chemin généré automatiquement par le Générateur de Classes.

"""

from typing import Any

from core.chemin import Chemin
from actions.simple.action_bouton import ActionBouton


class CheminVilleVersNonLance(Chemin):
    """Chemin: ville -> non_lance"""

    etat_initial = "ville"
    etat_sortie = "non_lance"

    def fonction_actions(self, manoir) -> list[Any]:
        """Retourne la séquence d'actions du chemin."""
        return [
            ActionBouton(manoir, "boutons/bouton_collecter.png", threshold=0.8),
        ]