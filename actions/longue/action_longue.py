# -*- coding: utf-8 -*-
"""ActionLongue - Séquence composite d'actions (atomique)"""
from actions.item import Item


class ActionLongue(Item):
    """Séquence composite d'actions traitée comme une unité atomique
    
    Une ActionLongue regroupe plusieurs actions qui doivent être
    exécutées ensemble sans interruption. C'est l'unité atomique
    pour les boucles : une boucle peut s'arrêter ENTRE les ActionLongue,
    mais pas AU MILIEU d'une ActionLongue.
    
    Exemple:
        # Tuer un mercenaire = séquence atomique de 5 clics
        ActionLongue(fenetre, [
            ActionOuvrirCarte(fenetre),
            ActionChercherMercenaire(fenetre),
            ActionSelectionner(fenetre),
            ActionEnvoyerTroupes(fenetre),
            ActionConfirmer(fenetre),
        ], nom="tuer_mercenaire")
    """
    
    def __init__(self, fenetre, actions, nom=None, condition_func=None,
                 maintenant=False, etat_requis=None):
        """
        Args:
            fenetre: Instance de FenetreBase
            actions: Liste d'actions composant la séquence
            nom: Nom optionnel pour le logging
            condition_func: Condition optionnelle pour exécuter la séquence
            maintenant: True import la liste a l'indexe actuel de fenetre.sequenceAction
                        False import la liste a la fin de fenetre.sequenceAction
            etat_requis: État dans lequel le manoir doit être pour exécuter
                         (le manoir navigue vers cet état avant d'ajouter l'action)
        """
        super().__init__(fenetre, condition_func)
        self.actions = actions if isinstance(actions, list) else [actions]
        self.nom = nom or "ActionLongue"
        self.maintenant = maintenant
        self.etat_requis = etat_requis
    
    def _run(self):
        """Ajoute toutes les sous-actions à la séquence (PROTÉGÉ)
        
        Les actions sont ajoutées juste après la position actuelle,
        donc elles seront exécutées immédiatement et dans l'ordre.
        
        Returns:
            bool: True (toujours succès, les erreurs sont gérées par les actions)
        """
        if self.actions:
            if self.maintenant:
                self.fenetre.sequence.add_next(self.actions)
                self.fenetre.logger.debug(
                    f"{self.nom}: {len(self.actions)} action(s) ajoutée(s) maintenant"
                    )
            else:
                self.fenetre.sequence.add(self.actions)
                self.fenetre.logger.debug(
                    f"{self.nom}: {len(self.actions)} action(s) ajoutée(s) a la fin"
                    )
        return True
    
    def __len__(self):
        """Retourne le nombre d'actions dans la séquence"""
        return len(self.actions)
    
    def __repr__(self):
        return f"ActionLongue('{self.nom}', actions={len(self.actions)})"

