# -*- coding: utf-8 -*-
"""Classe de base Item pour les actions et erreurs"""

from utils.logger import get_module_logger


class Item:
    """Classe de base pour les items exécutables (actions, erreurs)

    Attributes:
        fenetre: Instance du manoir/fenêtre associé
        condition_func: Fonction de condition optionnelle
        executer: Flag indiquant si l'item a été exécuté
        logger: Logger du module
    """

    def __init__(self, fenetre, condition_func=None):
        """
        Args:
            fenetre: Instance de ManoirBase ou FenetreBase
            condition_func: Fonction lambda() -> bool pour condition d'exécution
        """
        self.fenetre = fenetre
        self.condition_func = condition_func
        self.executer = False
        self.logger = get_module_logger(self.__class__.__name__)

    def condition(self) -> bool:
        """Vérifie si l'item doit être exécuté

        Returns:
            bool: True si la condition est remplie ou pas de condition
        """
        if self.condition_func is None:
            return True

        try:
            return self.condition_func()
        except Exception as e:
            self.logger.error(f"Erreur évaluation condition: {e}")
            return False

    def reset_condition(self):
        """Réinitialise le flag d'exécution"""
        self.executer = False

    def execute(self):
        """Exécute l'item

        À surcharger dans les sous-classes.

        Returns:
            bool: True si succès
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} doit implémenter execute()"
        )

    def __repr__(self):
        return f"{self.__class__.__name__}(fenetre={self.fenetre.nom if hasattr(self.fenetre, 'nom') else 'N/A'})"
