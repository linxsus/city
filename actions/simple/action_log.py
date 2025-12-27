"""
Created on Sun Dec  7 12:43:39 2025

@author: xavie
"""

from actions.action import Action


class ActionLog(Action):
    """Log un message (utile pour debug)

    Exemple:
        ActionLog(fenetre, "Début de la séquence de collecte")
    """

    def __init__(self, fenetre, message, level="info"):
        """
        Args:
            fenetre: Instance de FenetreBase
            message: Message à logger
            level: Niveau de log (debug, info, warning, error)
        """
        super().__init__(fenetre)
        self.message = message
        self.level = level.lower()

    def _run(self):
        """Log le message"""
        log_func = getattr(self.fenetre.logger, self.level, self.fenetre.logger.info)
        log_func(self.message)
        return True

    def __repr__(self):
        return f"ActionLog('{self.message[:30]}...')"
