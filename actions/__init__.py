"""Package actions - Système d'actions du framework"""

__all__ = [
    # Classes de base
    "Item",
    "SequenceActions",
    "Action",
    "ActionSimple",
    # Actions conditionnelles
    "ActionIf",
    "ActionIfElse",
    "ActionSwitch",
    # Actions de boucle
    "ActionFor",
    "ActionWhile",
    # Actions longues
    "ActionLongue",
    "ActionLogPeriodique",
    # Actions simples
    "ActionAttendre",
    "ActionLog",
    # Helpers de conditions
    "image_presente",
    "image_absente",
    "texte_present",
    "texte_absent",
    "variable_egale",
    "variable_superieure",
    "variable_inferieure",
    "variable_superieure_ou_egale",
    "variable_inferieure_ou_egale",
    "et",
    "ou",
    "non",
    "toujours_vrai",
    "toujours_faux",
]

# Classes de base
from actions.action import Action, ActionSimple

# Actions conditionnelles (depuis sous-package boucle)
from actions.boucle.action_if import ActionIf, ActionIfElse

# Actions de boucle (depuis sous-package boucle)
from actions.boucle.action_loops import ActionFor, ActionWhile
from actions.boucle.action_switch import ActionSwitch

# Helpers de conditions
from actions.item import (
    Item,
    et,
    image_absente,
    image_presente,
    non,
    ou,
    texte_absent,
    texte_present,
    toujours_faux,
    toujours_vrai,
    variable_egale,
    variable_inferieure,
    variable_inferieure_ou_egale,
    variable_superieure,
    variable_superieure_ou_egale,
)
from actions.longue.action_log_periodique import ActionLogPeriodique

# Actions longues (depuis sous-package longue)
from actions.longue.action_longue import ActionLongue
from actions.sequence_actions import SequenceActions

# Actions simples (depuis sous-package simple)
from actions.simple.action_attendre import ActionAttendre
from actions.simple.action_log import ActionLog
