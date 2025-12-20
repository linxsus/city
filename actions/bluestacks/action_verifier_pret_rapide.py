# -*- coding: utf-8 -*-
"""Action pour vérifier rapidement si le jeu est déjà chargé (une seule fois)"""

from actions.action import Action


class ActionVerifierPretRapide(Action):
    """Vérification rapide et unique si le jeu est déjà chargé

    Utilisée au début de la séquence de lancement pour détecter
    si BlueStacks est déjà ouvert et le jeu déjà chargé.

    - Si icone_jeu_charge.png détectée → signaler_jeu_charge() + casser séquence
    - Sinon → continuer la séquence normalement (attente + boucle)

    Contrairement à ActionVerifierPret :
    - Ne demande PAS de rotation
    - S'exécute UNE SEULE fois
    - Casse la séquence si le jeu est prêt (pour skip l'attente de 300s)
    """

    # Template UNIQUE pour détecter que le jeu est prêt
    TEMPLATE_JEU_CHARGE = "ville/icone_jeu_charge.png"

    def __init__(self, manoir, threshold=0.7):
        """
        Args:
            manoir: Manoir parent
            threshold: Seuil de détection (0-1)
        """
        super().__init__(manoir, log_erreur_si_echec=False)
        self.nom = "VerifierPretRapide"
        self.threshold = threshold

    def condition(self):
        """Toujours exécuter cette vérification"""
        return True

    def _gerer_popups_demarrage(self):
        """Gère les popups courants de démarrage (PROTÉGÉ)

        Vérifie et ferme les popups de démarrage courants :
        - Connexion quotidienne
        - Rapport de développement
        - Bouton gratuit

        Returns:
            int: Nombre de popups détectés et traités
        """
        import time

        popups_traites = 0
        max_tentatives = 3  # Maximum 3 popups à la suite

        for _ in range(max_tentatives):
            popup_trouve = False

            # 1. Connexion quotidienne
            if self.fenetre.detect_image("popups/connexion_quotidienne.png", threshold=0.6):
                self.logger.info(f"{self.fenetre.nom}: Popup 'Connexion Quotidienne' détecté")

                # Chercher le bouton Collecter
                bouton_pos = self.fenetre.find_image("boutons/bouton_collecter.png", threshold=0.6)
                if bouton_pos:
                    self.fenetre.click_at(*bouton_pos)
                else:
                    # Position estimée
                    x = int(self.fenetre.largeur * 0.5)
                    y = int(self.fenetre.hauteur * 0.85)
                    self.fenetre.click_at(x, y)

                time.sleep(1.5)
                popups_traites += 1
                popup_trouve = True

            # 2. Rapport de développement
            elif self.fenetre.detect_image("popups/rapport_developpement.png", threshold=0.7):
                self.logger.info(f"{self.fenetre.nom}: Popup 'Rapport Développement' détecté")

                # Cliquer sur la croix (en haut à droite)
                x = int(self.fenetre.largeur * 0.95)
                y = int(self.fenetre.hauteur * 0.05)
                self.fenetre.click_at(x, y)

                time.sleep(1.5)
                popups_traites += 1
                popup_trouve = True

            # 3. Bouton gratuit
            elif self.fenetre.detect_image("boutons/bouton_gratuit.png", threshold=0.7):
                self.logger.info(f"{self.fenetre.nom}: 'Bouton Gratuit' détecté")

                bouton_pos = self.fenetre.find_image("boutons/bouton_gratuit.png", threshold=0.7)
                if bouton_pos:
                    self.fenetre.click_at(*bouton_pos)
                    time.sleep(1.5)
                    popups_traites += 1
                    popup_trouve = True

            # Si aucun popup trouvé, arrêter la boucle
            if not popup_trouve:
                break

            # Re-capturer pour le prochain tour
            self.fenetre.capture(force=True)

        return popups_traites

    def _run(self):
        """Vérifie UNE FOIS si le jeu est déjà chargé

        Returns:
            bool: True (toujours)
        """
        # Vérifier si la fenêtre Windows existe
        if not self.fenetre.is_valid():
            self.logger.debug(f"{self.fenetre.nom}: Fenêtre non trouvée - skip vérification rapide")
            return True

        # Placer la fenêtre si position configurée
        if hasattr(self.fenetre, 'placer_fenetre'):
            if self.fenetre.position_x is not None or self.fenetre.position_y is not None:
                self.fenetre.placer_fenetre()

        # Activer la fenêtre
        self.fenetre.activate()

        # Capturer l'écran
        capture = self.fenetre.capture(force=True)
        if capture is None:
            self.logger.debug(f"{self.fenetre.nom}: Impossible de capturer - skip vérification rapide")
            return True

        # Chercher icone_jeu_charge.png
        icone_presente = self.fenetre.detect_image(self.TEMPLATE_JEU_CHARGE, threshold=self.threshold)

        if icone_presente:
            # Jeu déjà chargé et prêt !
            self.logger.info(f"{self.fenetre.nom}: Jeu DÉJÀ PRÊT détecté - vérification des popups de démarrage")

            # AVANT de signaler que le jeu est prêt, gérer les popups de démarrage
            popups_detectes = self._gerer_popups_demarrage()

            if popups_detectes:
                self.logger.info(f"{self.fenetre.nom}: {popups_detectes} popup(s) traité(s)")

            # Informer le manoir que le jeu est prêt
            if hasattr(self.fenetre, 'signaler_jeu_charge'):
                self.fenetre.signaler_jeu_charge()

            # Casser la séquence pour éviter l'attente de 300s
            self.fenetre.sequence.clear()

            return True
        else:
            # Jeu pas encore prêt, continuer normalement
            self.logger.info(f"{self.fenetre.nom}: Jeu non prêt - lancement de la séquence d'attente")
            return True

    def __repr__(self):
        return f"ActionVerifierPretRapide({self.fenetre.nom})"
