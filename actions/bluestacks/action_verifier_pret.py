# -*- coding: utf-8 -*-
"""Action pour vérifier si le jeu est chargé (icone_jeu_charge.png)"""
import time

from actions.action import Action


class ActionVerifierPret(Action):
    """Vérifie si le jeu est chargé (icone_jeu_charge.png uniquement)

    Action non bloquante utilisée dans une boucle ActionWhile.

    - Si icone_jeu_charge.png détectée → signaler_jeu_charge() → retourne True
    - Sinon → demande_rotation() pour passer au manoir suivant → retourne True

    La boucle ActionWhile continue tant que le jeu n'est pas prêt.
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
        self.nom = "VerifierPret"
        self.threshold = threshold
        self._dernier_log = 0
        self._intervalle_log = 10  # Log toutes les 10 secondes max

        # Variables pour les 2 vérifications espacées
        self._premiere_detection = None  # Timestamp de la 1ère détection
        self._delai_verification = 30  # 30 secondes entre les 2 vérifications
        self._icone_detectee_une_fois = False

    def condition(self):
        """Toujours exécuter cette vérification"""
        return True

    def _run(self):
        """Vérifie si le jeu est chargé avec 2 vérifications espacées de 30 secondes

        Returns:
            bool: True (l'action s'exécute toujours correctement)
        """
        # Vérifier d'abord si la fenêtre Windows existe
        if not self.fenetre.is_valid():
            self._log_attente("Fenêtre BlueStacks non trouvée")
            self.fenetre.demander_rotation()
            return True

        # Placer la fenêtre si position configurée (une seule fois)
        if not self._icone_detectee_une_fois and hasattr(self.fenetre, 'placer_fenetre'):
            if self.fenetre.position_x is not None or self.fenetre.position_y is not None:
                self.fenetre.placer_fenetre()

        # Activer la fenêtre pour la mettre au premier plan
        self.fenetre.activate()

        # Capturer l'écran
        capture = self.fenetre.capture(force=True)
        if capture is None:
            self._log_attente("Impossible de capturer l'écran")
            self.fenetre.demander_rotation()
            return True

        # VÉRIFIER SI UN POPUP A ÉTÉ DÉTECTÉ
        # Si oui, cela signifie que le jeu n'est pas stable → RESET
        if hasattr(self.fenetre, '_popup_detecte_pendant_lancement') and self.fenetre._popup_detecte_pendant_lancement:
            if self._icone_detectee_une_fois:
                self.logger.warning("Popup détecté pendant vérification - RESET de la vérification")
                self._icone_detectee_une_fois = False
                self._premiere_detection = None
            # Réinitialiser le flag pour la prochaine fois
            if hasattr(self.fenetre, 'reset_flag_popup'):
                self.fenetre.reset_flag_popup()

        # Chercher icone_jeu_charge.png
        icone_presente = self.fenetre.detect_image(self.TEMPLATE_JEU_CHARGE, threshold=self.threshold)

        if icone_presente:
            # Première détection
            if not self._icone_detectee_une_fois:
                self._icone_detectee_une_fois = True
                self._premiere_detection = time.time()
                self.logger.info(f"1ère détection de {self.TEMPLATE_JEU_CHARGE} - attente de {self._delai_verification}s pour confirmation")
                self.fenetre.demander_rotation()
                return True

            # Deuxième vérification : on attend que le délai soit écoulé
            temps_ecoule = time.time() - self._premiere_detection
            if temps_ecoule >= self._delai_verification:
                # Jeu stable et prêt !
                self.logger.info(f"2ème détection après {temps_ecoule:.1f}s - Jeu stable et prêt !")

                # Informer le manoir que le jeu est vraiment prêt
                if hasattr(self.fenetre, 'signaler_jeu_charge'):
                    self.fenetre.signaler_jeu_charge()

                return True
            else:
                # On attend encore
                restant = self._delai_verification - temps_ecoule
                self._log_attente(f"Attente confirmation ({restant:.1f}s restantes)")
                self.fenetre.demander_rotation()
                return True

        else:
            # Icône non détectée
            if self._icone_detectee_une_fois:
                # L'icône avait été détectée mais a disparu - RESET
                self.logger.warning("Icône perdue après 1ère détection - RESET")
                self._icone_detectee_une_fois = False
                self._premiere_detection = None

            self._log_attente("icone_jeu_charge.png non détectée")
            self.fenetre.demander_rotation()
            return True

    def _log_attente(self, message):
        """Log avec limitation de fréquence pour éviter le spam"""
        now = time.time()
        if now - self._dernier_log >= self._intervalle_log:
            self.logger.info(f"[{self.fenetre.nom}] {message}")
            self._dernier_log = now

    def __repr__(self):
        return f"ActionVerifierPret({self.fenetre.nom})"
