# -*- coding: utf-8 -*-
"""Action pour vérifier le timeout de lancement"""

from actions.action import Action


class ActionVerifierTimeout(Action):
    """Vérifie si le timeout de lancement est atteint

    Action utilisée dans la boucle ActionWhile de lancement.

    Si le timeout est atteint :
    - Sauvegarde l'écran et le log via signaler_timeout()
    - Retourne False pour signaler l'échec

    Sinon :
    - Demande rotation pour passer au manoir suivant
    - Retourne True (boucle continue)
    """

    def __init__(self, manoir):
        """
        Args:
            manoir: Manoir parent
        """
        super().__init__(manoir, log_erreur_si_echec=False)
        self.nom = "VerifierTimeout"

    def condition(self):
        """Toujours exécuter cette vérification"""
        return True

    def _run(self):
        """Vérifie le timeout

        Returns:
            bool: True si pas de timeout, False si timeout atteint
        """
        temps_ecoule = self.fenetre.get_temps_depuis_lancement()
        timeout = self.fenetre.TIMEOUT_LANCEMENT

        if temps_ecoule >= timeout:
            # Timeout atteint !
            self.logger.error(
                f"TIMEOUT: {temps_ecoule:.0f}s >= {timeout}s ({timeout // 60} min)"
            )
            self.fenetre._ajouter_historique(
                f"TIMEOUT: {temps_ecoule:.0f}s écoulées (limite: {timeout}s)"
            )

            # Signaler le timeout (sauvegarde écran + log + état BLOQUE)
            if hasattr(self.fenetre, 'signaler_timeout'):
                self.fenetre.signaler_timeout()

            return False

        # Pas de timeout → demander rotation
        self.fenetre.demander_rotation()
        return True

    def __repr__(self):
        temps = self.fenetre.get_temps_depuis_lancement()
        return f"ActionVerifierTimeout({self.fenetre.nom}, {temps:.0f}s)"
