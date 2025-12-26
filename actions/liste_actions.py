# -*- coding: utf-8 -*-
"""Point d'entrée centralisé pour toutes les actions du framework

Usage recommandé:
    import actions.liste_actions as ListeActions
    
    action = ListeActions.ActionAttendre(fenetre, 5)
    boucle = ListeActions.ActionFor(fenetre, 3, [...])
"""

# Classes de base
from .item import Item
from .action import Action, ActionSimple
from .sequence_actions import SequenceActions

# Actions simples
from .simple.action_attendre import ActionAttendre
from .simple.action_bouton import ActionBouton
from .simple.action_log import ActionLog

# Actions conditionnelles et boucles
from .boucle.action_if import ActionIf, ActionIfElse
from .boucle.action_loops import ActionFor, ActionWhile
from .boucle.action_switch import ActionSwitch

# Actions longues/composites
from .longue.action_longue import ActionLongue
from .longue.action_log_periodique import ActionLogPeriodique

# Helpers de conditions
from .item import (
    image_presente,
    image_absente,
    texte_present,
    texte_absent,
    variable_egale,
    variable_superieure,
    variable_inferieure,
    variable_superieure_ou_egale,
    variable_inferieure_ou_egale,
    et,
    ou,
    non,
    toujours_vrai,
    toujours_faux,
)

__all__ = [
    # Classes de base
    'Item',
    'Action',
    'ActionSimple',
    'SequenceActions',
    # Actions simples
    'ActionAttendre',
    'ActionBouton',
    'ActionLog',
    # Actions conditionnelles et boucles
    'ActionIf',
    'ActionIfElse',
    'ActionFor',
    'ActionWhile',
    'ActionSwitch',
    # Actions longues
    'ActionLongue',
    'ActionLogPeriodique',
    # Helpers de conditions
    'image_presente',
    'image_absente',
    'texte_present',
    'texte_absent',
    'variable_egale',
    'variable_superieure',
    'variable_inferieure',
    'variable_superieure_ou_egale',
    'variable_inferieure_ou_egale',
    'et',
    'ou',
    'non',
    'toujours_vrai',
    'toujours_faux',
] 


