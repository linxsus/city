# -*- coding: utf-8 -*-
"""Action de clic sur une image (bouton)"""

from actions.action import Action


class ActionBouton(Action):
    """Effectue un clic sur une image template

    Utilise la détection visuelle pour trouver l'image et clique dessus.

    Exemple:
        ActionBouton(manoir, "boutons/bouton_gratuit.png")
        ActionBouton(manoir, "popups/fermer.png", offset=(10, 0))
    """

    def __init__(self, fenetre, template_path, offset=(0, 0), threshold=None, **kwargs):
        """
        Args:
            fenetre: Instance de ManoirBase ou FenetreBase
            template_path: Chemin vers l'image template (relatif à templates/)
            offset: Décalage (dx, dy) par rapport au centre de l'image trouvée
            threshold: Seuil de confiance (0-1), None pour utiliser la valeur par défaut
            **kwargs: Arguments passés à Action (erreurs_verif_apres, etc.)
        """
        super().__init__(fenetre, **kwargs)
        self.template_path = template_path
        self.offset = offset
        self.threshold = threshold

    def _run(self):
        """Trouve l'image et clique dessus

        Returns:
            bool: True si l'image a été trouvée et cliquée, False sinon
        """
        result = self.fenetre.click_image(
            self.template_path,
            threshold=self.threshold,
            offset=self.offset
        )

        if result:
            self.logger.debug(f"Clic sur {self.template_path}")
        else:
            self.logger.warning(f"Image non trouvée: {self.template_path}")

        return result

    def __repr__(self):
        return f"ActionBouton({self.template_path})"
