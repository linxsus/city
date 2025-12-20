# -*- coding: utf-8 -*-
"""Action pour lancer BlueStacks via raccourci/commande"""
import time
import subprocess

from actions.action import Action


class ActionLancerRaccourci(Action):
    """Lance BlueStacks via le raccourci/commande configuré

    Utilise la commande de lancement configurée dans le manoir.
    Si BlueStacks est déjà ouvert, ne fait rien.
    """

    def __init__(self, manoir):
        """
        Args:
            manoir: Manoir parent (doit avoir commande_lancement)
        """
        super().__init__(manoir)
        self.nom = "LancerRaccourci"

    def condition(self):
        """Toujours exécuter"""
        return True

    def _run(self):
        """Lance BlueStacks

        Returns:
            bool: True si lancé ou déjà ouvert
        """
        # Si déjà ouvert, on passe
        if self.fenetre.est_fenetre_ouverte():
            self.logger.info(f"{self.fenetre.nom}: fenêtre déjà ouverte")
            self.fenetre._ajouter_historique("Fenêtre déjà ouverte")
            return True

        # Vérifier qu'on a une commande de lancement
        if not self.fenetre.commande_lancement:
            self.logger.error("Pas de commande de lancement configurée")
            self.fenetre._ajouter_historique("ERREUR: Pas de commande de lancement")
            return False

        self.logger.info(f"Lancement de {self.fenetre.nom}...")
        self.fenetre._ajouter_historique(f"Lancement: {self.fenetre.commande_lancement}")

        try:
            # Construire la commande en string pour shell=True
            cmd_parts = []
            for part in self.fenetre.commande_lancement:
                if ' ' in part and not part.startswith('"'):
                    cmd_parts.append(f'"{part}"')
                else:
                    cmd_parts.append(part)

            cmd_str = ' '.join(cmd_parts)
            self.logger.info(f"Commande: {cmd_str}")

            # Lancer BlueStacks en arrière-plan
            process = subprocess.Popen(
                cmd_str,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True
            )

            time.sleep(0.5)

            if process.poll() is not None:
                stdout, stderr = process.communicate()
                if stderr:
                    self.logger.error(
                        f"Erreur lancement: {stderr.decode('utf-8', errors='ignore')}"
                    )
                self.fenetre._ajouter_historique("ERREUR: Processus terminé immédiatement")
                return False

            self.logger.info(
                f"{self.fenetre.nom}: lancement initié (PID: {process.pid})"
            )
            self.fenetre._ajouter_historique(f"Processus lancé (PID: {process.pid})")
            return True

        except FileNotFoundError as e:
            self.logger.error(f"Exécutable non trouvé: {e}")
            self.fenetre._ajouter_historique(f"ERREUR: Exécutable non trouvé - {e}")
            return False
        except Exception as e:
            self.logger.error(f"Erreur lancement: {e}")
            self.fenetre._ajouter_historique(f"ERREUR: {e}")
            return False

    def __repr__(self):
        return f"ActionLancerRaccourci({self.fenetre.nom})"
