"""Action spéciale pour demander la reprise de preparer_tour()

Cette action signale à l'Engine qu'il doit rappeler preparer_tour() du manoir.
Utilisée quand un chemin de navigation est incertain et nécessite une
redétermination de l'état après exécution partielle.
"""

from actions.action import Action


class ActionReprisePreparerTour(Action):
    """Action de reprise pour les chemins incertains

    Quand un chemin de navigation est incomplet (sortie incertaine),
    cette action est ajoutée à la fin de la séquence pour signaler
    à l'Engine de rappeler preparer_tour() du manoir.

    L'Engine vérifie `action.demande_reprise` après chaque action
    et rappelle preparer_tour() si True.

    Contraintes d'utilisation :
    - Doit être la dernière action de la séquence
    - Il ne peut y en avoir qu'une seule par séquence
    """

    # Flag vérifié par l'Engine
    demande_reprise = True

    def __init__(self, manoir):
        """
        Args:
            manoir: Instance du manoir
        """
        super().__init__(manoir, log_erreur_si_echec=False)
        self.nom = "ReprisePreparerTour"

    def condition(self):
        """Toujours exécuter cette action"""
        return True

    def _run(self):
        """Exécution : ne fait rien, le flag demande_reprise suffit

        Returns:
            bool: True (toujours succès)
        """
        self.logger.debug(f"[{self.fenetre.nom}] Demande de reprise preparer_tour()")
        return True

    def __repr__(self):
        return f"ActionReprisePreparerTour({self.fenetre.nom})"
