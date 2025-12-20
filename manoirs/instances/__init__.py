# -*- coding: utf-8 -*-
"""Instances concrètes de manoirs"""

from manoirs.instances.manoir_virtuel import ManoirVirtuel, creer_manoir_virtuel
from manoirs.instances.manoir_bluestacks import (
    ManoirBlueStacks,
    EtatBlueStacks,
)

# Les actions sont maintenant dans actions/bluestacks/ et actions/popups/
# Importer depuis là directement :
# from actions.bluestacks import ActionLancerRaccourci, ActionVerifierPret, ActionVerifierTimeout
# from actions.popups import ActionFermerRapportDeveloppement, ...
