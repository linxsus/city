"""Manoir Principal - Gestion du compte principal avec BlueStacks"""

import actions.liste_actions as ListeActions
from manoirs.instances.manoir_bluestacks import ManoirBlueStacks


class ManoirPrincipal(ManoirBlueStacks):
    """Manoir Principal - Lance BlueStacks et exécute une action toutes les 5 minutes

    Ce manoir :
    1. Lance automatiquement BlueStacks
    2. Attend que le jeu soit chargé
    3. Exécute une action toutes les 5 minutes qui affiche "je suis la" dans les logs
    """

    def __init__(self, manoir_id="principal", config=None):
        """Initialise le manoir principal

        Args:
            manoir_id: Identifiant du manoir
            config: Configuration (chargée depuis config_manoirs si None)
        """
        # Appeler le constructeur de ManoirBlueStacks
        super().__init__(manoir_id=manoir_id, config=config)

        self.logger.info(f"Manoir Principal '{self.nom}' initialisé")
        self.debut = True

    def definir_timers(self):
        """Définit les timers pour ce manoir - Pas de timers pour ce manoir simple"""
        # Pas de timers nécessaires, tout est géré par la boucle d'actions
        pass

    def gestion_tour(self):
        """Logique métier du manoir - Appelée quand BlueStacks est PRET

        Crée une boucle infinie qui affiche "je suis la" toutes les 30 secondes.
        """
        # Vérifier si la séquence est vide (premier appel après passage en PRET)
        if self.debut:
            # Créer une boucle infinie qui s'exécute toujours
            boucle_principale = ListeActions.ActionWhile(
                self,
                condition_func=lambda m: True,  # Toujours True = boucle infinie
                actions=[
                    # Attendre 30 secondes
                    ListeActions.ActionAttendre(self, 30),
                    # Afficher le message
                    ListeActions.ActionLog(self, "je suis la", level="info"),
                ],
                max_iterations=None,  # Pas de limite
                nom_boucle="boucle_principale",
            )

            self.sequence.add(boucle_principale)
            self.logger.debug("Boucle principale ajoutée à la séquence")
            self.debut = False

    def get_prochain_passage_prioritaire(self):
        """Retourne toujours float('inf') car pas d'actions prioritaires

        Returns:
            float: float('inf') - pas d'actions prioritaires
        """
        return float("inf")

    def get_prochain_passage_normal(self):
        """Retourne 0 si on doit traiter ce manoir, sinon le temps avant le prochain timer

        Returns:
            float: 0 si prêt maintenant, sinon temps avant prochain timer
        """
        # Toujours retourner 0 pour que le manoir soit traité
        # preparer_tour() gérera le lancement et l'état
        return 0
