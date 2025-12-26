# -*- coding: utf-8 -*-
"""Package actions - Système d'actions du framework"""

# Classes de base
from actions.item import Item
from actions.sequence_actions import SequenceActions
from actions.action import Action, ActionSimple

# Actions conditionnelles (depuis sous-package boucle)
from actions.boucle.action_if import ActionIf, ActionIfElse
from actions.boucle.action_switch import ActionSwitch

# Actions de boucle (depuis sous-package boucle)
from actions.boucle.action_loops import ActionFor, ActionWhile

# Actions longues (depuis sous-package longue)
from actions.longue.action_longue import ActionLongue
from actions.longue.action_log_periodique import ActionLogPeriodique

# Actions simples (depuis sous-package simple)
from actions.simple.action_attendre import ActionAttendre
from actions.simple.action_log import ActionLog

# Helpers de conditions
from actions.item import (
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
