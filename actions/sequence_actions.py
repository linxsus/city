# -*- coding: utf-8 -*-
"""Gestion de séquences d'actions avec historique"""


class SequenceActions:
    """Liste ordonnée d'actions avec index persistant et historique
    
    La séquence persiste entre les tours de la fenêtre.
    L'index indique la prochaine action à exécuter.
    Les 20 dernières actions exécutées sont conservées dans l'historique.
    
    Attributes:
        actions: Liste des actions
        index: Index de la prochaine action à exécuter
        fin: Flag indiquant si la séquence est terminée
    """
    
    HISTORIQUE_MAX = 20  # Nombre d'actions passées à conserver
    
    def __init__(self):
        self.actions = []
        self.index = 0
        self.fin = False
    
    def add(self, new, position=None):
        """Ajoute une ou plusieurs actions à la séquence 
        
        Args:
            new: Action unique ou liste d'actions
            position: Position d'insertion (None = à la fin)
        
        """
        if not isinstance(new, list):
            new = [new]
        
        for act in new:
            
            if position is None:
                self.actions.append(act)
            else:
                # Contraindre la position aux bornes valides
                pos = max(self.index, min(position, len(self.actions)))
                self.actions.insert(pos, act)
                position += 1
        
        
        # Réinitialiser le flag fin si on ajoute des actions
        if not self.is_end():
            self.fin = False
    
    def add_next(self, new):
        """Ajoute des actions juste après la position actuelle
        
        Args:
            new: Action unique ou liste d'actions
        """
        self.add(new, position=self.index)
    
    def __iter__(self):
        """Rend la séquence itérable"""
        return self
    
    def __next__(self):
        """Retourne la prochaine action et avance l'index
        
        Returns:
            Item: Prochaine action à exécuter
            
        Raises:
            StopIteration: Si la séquence est terminée
        """
        if self.index >= len(self.actions):
            self.fin = True
            raise StopIteration
        
        action = self.actions[self.index]
        self.index += 1
        
        # Nettoyer l'historique si trop grand
        self._nettoyer_historique()
        
        return action
    
    def _nettoyer_historique(self):
        """Supprime les actions trop anciennes de l'historique (PROTÉGÉ)
        
        Garde les HISTORIQUE_MAX dernières actions exécutées.
        """
        if self.index > self.HISTORIQUE_MAX:
            surplus = self.index - self.HISTORIQUE_MAX
            self.actions = self.actions[surplus:]
            self.index = self.HISTORIQUE_MAX
    
    def is_end(self):
        """Vérifie si la séquence est terminée
        
        Returns:
            bool: True si toutes les actions ont été exécutées
        """
        return self.index >= len(self.actions)
    
    def get_current(self):
        """Retourne l'action courante sans avancer l'index
        
        Returns:
            Item ou None: Action courante ou None si terminée
        """
        if self.index >= len(self.actions):
            return None
        return self.actions[self.index]
    
    def get_historique(self):
        """Retourne l'historique des actions exécutées
        
        Returns:
            list: Actions avant l'index actuel (max HISTORIQUE_MAX)
        """
        debut = max(0, self.index - self.HISTORIQUE_MAX)
        return self.actions[debut:self.index]
    
    def get_futures(self):
        """Retourne les actions restantes à exécuter
        
        Returns:
            list: Actions à partir de l'index actuel
        """
        return self.actions[self.index:]
    
        
    def rewind(self, n=1):
        """Recule l'index de n positions
        
        Args:
            n: Nombre de positions à reculer
        """
        self.index = max(0, self.index - n)
        self.fin = False
    
    def skip(self, n=1):
        """Avance l'index de n positions sans exécuter
        
        Args:
            n: Nombre de positions à sauter
        """
        self.index = min(len(self.actions), self.index + n)
    
    def clear(self):
        """Supprime les actions futures (garde l'historique)"""
        self.actions = self.actions[:self.index]
        self.fin = True
    
    def __len__(self):
        """Retourne le nombre total d'actions
        
        Returns:
            int: Nombre d'actions dans la séquence
        """
        return len(self.actions)
    
    def remaining(self):
        """Retourne le nombre d'actions restantes
        
        Returns:
            int: Nombre d'actions à exécuter
        """
        return max(0, len(self.actions) - self.index)
    
    def __repr__(self):
        return (
            f"SequenceActions(total={len(self.actions)}, "
            f"index={self.index}, remaining={self.remaining()})"
        )
