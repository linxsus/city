# -*- coding: utf-8 -*-
"""
Created on Sun Dec  7 15:15:26 2025

@author: xavie
"""

from actions.longue.action_longue import ActionLongue
from actions.boucle.action_loops import ActionWhile
from actions.simple.action_attendre import ActionAttendre
from actions.simple.action_log import ActionLog
from actions.item import toujours_vrai


class ActionLogPeriodique(ActionLongue):
    def __init__(self, fenetre, message="log periodique", duree_secondes=20, nom="log periodique", max_iterations=1000):
        actions_list = [
            ActionWhile(
                fenetre,
                condition_func=toujours_vrai(),
                actions=[
                    ActionAttendre(fenetre, duree_secondes=duree_secondes),
                    ActionLog(fenetre, message)
                ],
                max_iterations=max_iterations,
                nom_boucle="Afficher Log"
            )
        ]
        super().__init__(fenetre, actions_list, nom=nom)
