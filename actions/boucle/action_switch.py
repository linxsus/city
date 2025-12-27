"""Action Switch pour branchement multiple"""

from actions.item import Item


class ActionSwitch(Item):
    """Branchement multiple selon une valeur (switch/case)

    Évalue une fonction et ajoute les actions correspondantes
    au cas trouvé dans le dictionnaire.

    Exemple:
        ActionSwitch(
            fenetre,
            valeur_func=lambda f: f.etat_jeu,
            cas_dict={
                "menu": [ActionEntrerJeu(fenetre)],
                "ville": [ActionCollecter(fenetre), ActionConstruire(fenetre)],
                "combat": [ActionFuir(fenetre)],
            },
            default=[ActionAttendre(fenetre, 5)]
        )
    """

    def __init__(self, fenetre, valeur_func, cas_dict, default=None):
        """
        Args:
            fenetre: Instance de FenetreBase
            valeur_func: Fonction lambda(fenetre) -> valeur
            cas_dict: Dictionnaire {valeur: [actions]}
            default: Actions par défaut si valeur non trouvée
        """
        super().__init__(fenetre)
        self.valeur_func = valeur_func
        self.cas_dict = cas_dict
        self.default = default or []
        if not isinstance(self.default, list):
            self.default = [self.default]

        # Normaliser les valeurs du dictionnaire
        for key in self.cas_dict:
            if not isinstance(self.cas_dict[key], list):
                self.cas_dict[key] = [self.cas_dict[key]]

    def _run(self):
        """Évalue la valeur et ajoute les actions correspondantes (PROTÉGÉ)

        Returns:
            bool: True (toujours succès)
        """
        # Évaluer la valeur
        valeur = self.valeur_func(self.fenetre)

        # Trouver les actions correspondantes
        actions = self.cas_dict.get(valeur, self.default)

        # Ajouter les actions
        if actions:
            self.fenetre.sequence.add_next(actions)
            self.logger.debug(f"ActionSwitch: cas '{valeur}', {len(actions)} action(s) ajoutée(s)")
        else:
            self.logger.debug(f"ActionSwitch: cas '{valeur}', aucune action")

        return True

    def __repr__(self):
        cas = list(self.cas_dict.keys())
        return f"ActionSwitch(cas={cas})"
