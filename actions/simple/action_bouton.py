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
        self._position = None

    def condition(self):
        """Vérifie que l'image est visible et stocke sa position

        Returns:
            bool: True si condition parent OK et image visible
        """
        if not super().condition():
            return False
        self._position = self.fenetre.find_image(self.template_path, self.threshold)
        return self._position is not None

    def _run(self):
        """Clique sur la position trouvée par condition()

        Returns:
            bool: True si clic effectué, False sinon
        """
        if not self._position:
            self.logger.warning(f"Image non trouvée: {self.template_path}")
            return False

        x, y = self._position
        self.fenetre.click_at(x + self.offset[0], y + self.offset[1])
        self.logger.debug(f"Clic sur {self.template_path}")
        return True

    def __repr__(self):
        return f"ActionBouton({self.template_path})"
