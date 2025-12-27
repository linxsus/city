"""Instances concrètes de manoirs"""

__all__ = [
    "ManoirVirtuel",
    "creer_manoir_virtuel",
    "ManoirBlueStacks",
    "EtatBlueStacks",
]

from manoirs.instances.manoir_bluestacks import (
    EtatBlueStacks,
    ManoirBlueStacks,
)
from manoirs.instances.manoir_virtuel import ManoirVirtuel, creer_manoir_virtuel

# Les actions sont maintenant dans actions/bluestacks/ et actions/popups/
# Importer depuis là directement :
# from actions.bluestacks import ActionLancerRaccourci, ActionVerifierPret, ActionVerifierTimeout
# from actions.popups import ActionFermerRapportDeveloppement, ...
