"""Chemin : Attendre pendant le chargement"""

from typing import Any, List

from actions.action_reprise_preparer_tour import ActionReprisePreparerTour
from actions.simple.action_attendre import ActionAttendre
from core.chemin import Chemin
from core.etat_inconnu import EtatInconnu


class CheminAttendreChargement(Chemin):
    """Chemin pour attendre pendant le chargement de BlueStacks

    chargement → inconnu (ville ou popups)

    Actions :
    1. Attend 5 secondes de manière non-bloquante
    2. ActionReprisePreparerTour pour re-détecter l'état après

    Note:
        L'attente est non-bloquante : permet au moteur de traiter
        d'autres fenêtres pendant ce temps.
    """

    etat_initial = "chargement"
    # Sortie incertaine : peut être ville ou popup
    etat_sortie = EtatInconnu(
        etats_possibles=["ville", "popup_rapport", "popup_connexion", "popup_gratuit"]
    )

    # Durée d'attente en secondes
    DUREE_ATTENTE = 5

    def fonction_actions(self, manoir) -> List[Any]:
        """Génère les actions pour attendre pendant le chargement

        Args:
            manoir: Instance du manoir

        Returns:
            Liste d'actions
        """
        return [
            ActionAttendre(manoir, self.DUREE_ATTENTE),
            ActionReprisePreparerTour(manoir),
        ]
