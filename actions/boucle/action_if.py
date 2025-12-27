"""Actions conditionnelles If et IfElse"""

from actions.item import Item


class ActionIf(Item):
    """Ajoute des actions à la séquence SI la condition est vraie

    Exemple:
        ActionIf(
            fenetre,
            condition_func=variable_superieure("energie", 50),
            actions_si_vrai=[ActionRecolter(fenetre), ActionConstruire(fenetre)]
        )
    """

    def __init__(self, fenetre, condition_func, actions_si_vrai):
        """
        Args:
            fenetre: Instance de FenetreBase
            condition_func: Fonction lambda(fenetre) -> bool
            actions_si_vrai: Liste d'actions à ajouter si condition vraie
        """
        super().__init__(fenetre, condition_func)
        self.actions_si_vrai = (
            actions_si_vrai if isinstance(actions_si_vrai, list) else [actions_si_vrai]
        )

    def _run(self):
        """Ajoute les actions si la condition est vraie (PROTÉGÉ)

        Returns:
            bool: True (toujours succès)
        """
        # La condition a déjà été évaluée dans execute()
        # Si on arrive ici, c'est que la condition est vraie
        self.fenetre.sequence.add_next(self.actions_si_vrai)
        self.logger.debug(f"ActionIf: {len(self.actions_si_vrai)} action(s) ajoutée(s)")
        return True

    def __repr__(self):
        return f"ActionIf(actions={len(self.actions_si_vrai)})"


class ActionIfElse(Item):
    """Branchement conditionnel complet (if/else)

    Ajoute des actions différentes selon que la condition est vraie ou fausse.

    Exemple:
        ActionIfElse(
            fenetre,
            condition_func=image_presente("templates/bouton_ok.png"),
            actions_si_vrai=[ActionCliquer(fenetre, x, y)],
            actions_si_faux=[ActionAttendre(fenetre, 5)]
        )
    """

    def __init__(self, fenetre, condition_func, actions_si_vrai, actions_si_faux):
        """
        Args:
            fenetre: Instance de FenetreBase
            condition_func: Fonction lambda(fenetre) -> bool
            actions_si_vrai: Actions si condition vraie
            actions_si_faux: Actions si condition fausse
        """
        super().__init__(fenetre, condition_func)
        self.actions_si_vrai = (
            actions_si_vrai if isinstance(actions_si_vrai, list) else [actions_si_vrai]
        )
        self.actions_si_faux = (
            actions_si_faux if isinstance(actions_si_faux, list) else [actions_si_faux]
        )

    def execute(self):
        """Override execute pour gérer les deux branches

        Returns:
            bool: True (toujours succès)
        """
        # Évaluer la condition
        condition_result = self.condition()

        # Choisir les actions appropriées
        if condition_result:
            actions = self.actions_si_vrai
            branche = "VRAI"
        else:
            actions = self.actions_si_faux
            branche = "FAUX"

        # Ajouter les actions
        self.fenetre.sequence.add_next(actions)
        self.logger.debug(f"ActionIfElse: branche {branche}, {len(actions)} action(s) ajoutée(s)")

        self.executer = True
        return True

    def _run(self):
        """Non utilisé car execute() est surchargé"""
        pass

    def __repr__(self):
        return (
            f"ActionIfElse(si_vrai={len(self.actions_si_vrai)}, "
            f"si_faux={len(self.actions_si_faux)})"
        )
