# -*- coding: utf-8 -*-
"""Manoir BlueStacks - Classe abstraite pour gérer une fenêtre BlueStacks

ManoirBlueStacks gère le cycle de vie d'une fenêtre BlueStacks :
- Lancement de l'instance
- Détection du chargement du jeu
- Gestion des popups de démarrage
- Timeout et récupération d'erreur

Les sous-classes doivent implémenter gestion_tour() pour la logique métier.
"""
import time
from abc import abstractmethod
from enum import Enum, auto

from manoirs.manoir_base import ManoirBase
from manoirs.config_manoirs import get_config, LARGEUR_DEFAUT, HAUTEUR_DEFAUT
import actions.liste_actions as ListeActions


class EtatBlueStacks(Enum):
    """États possibles du manoir BlueStacks"""
    NON_LANCE = auto()       # BlueStacks pas encore lancé
    LANCEMENT = auto()       # Séquence de lancement en cours (non bloquant)
    PRET = auto()            # Jeu chargé, prêt à automatiser
    BLOQUE = auto()          # Trop d'échecs, reboot nécessaire


class ManoirBlueStacks(ManoirBase):
    """Manoir BlueStacks - Gère une instance BlueStacks

    Classe abstraite qui gère le cycle de vie d'une fenêtre BlueStacks.
    Les sous-classes doivent implémenter gestion_tour() pour la logique métier.

    États:
    - NON_LANCE: BlueStacks pas lancé
    - LANCEMENT: Lancé, en attente de icone_jeu_charge.png
    - PRET: Jeu chargé, gestion_tour() appelée
    - BLOQUE: Timeout ou erreur, reboot au prochain tour

    Timeout:
    - 30 minutes pour atteindre l'état PRET
    - Inclut le temps de gestion des popups
    - En cas de timeout: sauvegarde écran + log détaillé
    """

    # Timeout de lancement en secondes (30 minutes)
    TIMEOUT_LANCEMENT = 30 * 60

    def __init__(self, manoir_id="bluestacks", config=None):
        """
        Args:
            manoir_id: Identifiant unique
            config: Configuration (dict) ou None pour charger depuis config_manoirs
        """
        if config is None:
            config = get_config(manoir_id) or {}

        super().__init__(
            manoir_id=manoir_id,
            nom=config.get("nom", "Manoir BlueStacks"),
            titre_bluestacks=config.get("titre_bluestacks", "BlueStacks App Player"),
            largeur=config.get("largeur", LARGEUR_DEFAUT),
            hauteur=config.get("hauteur", HAUTEUR_DEFAUT),
            priorite=config.get("priorite", 50),
            slots_config=config.get("slots_config"),
            position_x=config.get("position_x"),
            position_y=config.get("position_y"),
        )

        # Configuration spécifique
        self.commande_lancement = config.get("commande_lancement", [])
        self.temps_initialisation = config.get("temps_initialisation", 60)

        # État
        self._etat = EtatBlueStacks.NON_LANCE
        self._heure_lancement = None  # Timestamp du lancement

        # Flag pour détecter les popups pendant la vérification
        self._popup_detecte_pendant_lancement = False

        # Historique des actions pour le debug
        self._historique_actions = []

    @property
    def etat(self):
        """État actuel du manoir"""
        return self._etat

    @etat.setter
    def etat(self, nouvel_etat):
        """Change l'état avec log"""
        if nouvel_etat != self._etat:
            self.logger.info(f"{self.nom}: {self._etat.name} -> {nouvel_etat.name}")
            self._ajouter_historique(f"État: {self._etat.name} -> {nouvel_etat.name}")
            self._etat = nouvel_etat

    # =========================================================
    # HISTORIQUE DES ACTIONS (pour debug)
    # =========================================================

    def _ajouter_historique(self, message):
        """Ajoute un message à l'historique des actions

        Args:
            message: Message à ajouter
        """
        timestamp = time.strftime("%H:%M:%S")
        self._historique_actions.append(f"[{timestamp}] {message}")

        # Limiter la taille de l'historique
        if len(self._historique_actions) > 100:
            self._historique_actions = self._historique_actions[-100:]

    def get_historique_actions(self):
        """Retourne l'historique des actions

        Returns:
            list: Liste des messages d'historique
        """
        return self._historique_actions.copy()

    # =========================================================
    # SURCHARGE - Gestion propre des erreurs pendant le démarrage
    # =========================================================

    def capture(self, force=False):
        """Capture l'écran - silencieux si manoir pas prêt

        Autorise la capture pendant LANCEMENT car les actions en ont besoin.
        """
        if self._etat in (EtatBlueStacks.NON_LANCE, EtatBlueStacks.BLOQUE):
            return None
        return super().capture(force)

    def detect_image(self, template_path, threshold=None, region=None):
        """Détecte une image - silencieux si manoir pas prêt

        Autorise la détection pendant LANCEMENT car les actions en ont besoin.
        """
        if self._etat in (EtatBlueStacks.NON_LANCE, EtatBlueStacks.BLOQUE):
            return False
        return super().detect_image(template_path, threshold, region)

    def find_image(self, template_path, threshold=None, region=None):
        """Trouve une image - silencieux si manoir pas prêt

        Autorise la recherche pendant LANCEMENT car les actions en ont besoin.
        """
        if self._etat in (EtatBlueStacks.NON_LANCE, EtatBlueStacks.BLOQUE):
            return None
        return super().find_image(template_path, threshold, region)

    # =========================================================
    # LANCEMENT ET REBOOT
    # =========================================================

    def est_fenetre_ouverte(self):
        """Vérifie si la fenêtre BlueStacks est ouverte"""
        hwnd = self.find_window()
        return hwnd is not None

    def _reboot_bluestacks(self):
        """Reboot BlueStacks après un blocage

        Reset tous les flags et la séquence, puis repasse en NON_LANCE
        pour relancer le processus de lancement.
        """
        self.logger.warning(f"{self.nom}: Reboot en cours...")
        self._ajouter_historique("REBOOT: Réinitialisation complète")

        # TODO: Fermer BlueStacks proprement si possible
        # Pour l'instant on se contente de relancer

        # Reset des flags
        self._heure_lancement = None
        self._hwnd = None
        self._rect = None

        # Vider la séquence et l'historique
        self.sequence.clear()
        self._historique_actions.clear()

        # Passer à NON_LANCE pour relancer
        self.etat = EtatBlueStacks.NON_LANCE

    # =========================================================
    # GESTION DU TIMEOUT
    # =========================================================

    def get_temps_depuis_lancement(self):
        """Retourne le temps écoulé depuis le lancement

        Returns:
            float: Temps en secondes, ou 0 si pas lancé
        """
        if self._heure_lancement is None:
            return 0
        return time.time() - self._heure_lancement

    def est_timeout_atteint(self):
        """Vérifie si le timeout de lancement est atteint

        Returns:
            bool: True si timeout atteint
        """
        return self.get_temps_depuis_lancement() >= self.TIMEOUT_LANCEMENT

    def est_jeu_pret(self):
        """Vérifie si le jeu est prêt (état PRET)

        Returns:
            bool: True si état PRET
        """
        return self._etat == EtatBlueStacks.PRET

    def sauvegarder_etat_timeout(self):
        """Sauvegarde l'état complet lors d'un timeout

        Sauvegarde:
        - Screenshot de l'écran
        - Log de l'historique des actions

        Returns:
            Path: Chemin du screenshot sauvegardé
        """
        self.logger.error(f"{self.nom}: TIMEOUT après {self.TIMEOUT_LANCEMENT // 60} minutes")

        # Sauvegarder le screenshot
        screenshot_path = self.save_capture(suffix="_TIMEOUT")

        # Logger l'historique des actions
        self.logger.error("=== HISTORIQUE DES ACTIONS ===")
        for ligne in self._historique_actions:
            self.logger.error(ligne)
        self.logger.error("=== FIN HISTORIQUE ===")

        # Logger l'état actuel
        self.logger.error(f"État: {self._etat.name}")
        self.logger.error(f"Temps depuis lancement: {self.get_temps_depuis_lancement():.1f}s")
        self.logger.error(f"Séquence: {self.sequence}")

        return screenshot_path

    # =========================================================
    # IMPLÉMENTATION ABSTRAITE - preparer_tour
    # =========================================================

    def preparer_tour(self):
        """Prépare le tour et alimente la séquence

        Logique non bloquante :
        - NON_LANCE → Construit la séquence de lancement, passe en LANCEMENT
        - LANCEMENT → Laisse la séquence s'exécuter (ActionWhile gère la boucle)
        - PRET → Active la fenêtre et appelle gestion_tour()
        - BLOQUE → Reboot

        Returns:
            bool: True si prêt à exécuter, False sinon
        """
        # ===== ÉTAT: BLOQUE → Reboot =====
        if self._etat == EtatBlueStacks.BLOQUE:
            self._reboot_bluestacks()
            return False

        # ===== ÉTAT: NON_LANCE → Construire séquence de lancement =====
        if self._etat == EtatBlueStacks.NON_LANCE:
            self._heure_lancement = time.time()
            self._ajouter_historique("Lancement initié")
            self._construire_sequence_lancement()
            self.etat = EtatBlueStacks.LANCEMENT
            self.logger.info(f"{self.nom}: Séquence de lancement initiée")
            return True

        # ===== ÉTAT: LANCEMENT → Laisser la séquence s'exécuter =====
        if self._etat == EtatBlueStacks.LANCEMENT:
            # La séquence ActionWhile gère tout
            # signaler_jeu_charge() fera passer en état PRET
            return True

        # ===== ÉTAT: PRET → Appeler gestion_tour() =====
        if self._etat == EtatBlueStacks.PRET:
            self.activate()
            self.gestion_tour()
            return True

        return False

    def _construire_sequence_lancement(self):
        """Construit la séquence d'actions pour le lancement du jeu

        Séquence optimisée :
        1. ActionLancerRaccourci - Lance BlueStacks (skip si déjà ouvert)
        2. ActionVerifierPretRapide - Vérification rapide si déjà prêt (skip attente si OUI)
        3. ActionAttendre - Attend le temps d'initialisation (seulement si pas déjà prêt)
        4. ActionWhile - Boucle tant que pas prêt et pas timeout :
            - ActionVerifierPret - Vérifie icone_jeu_charge.png
            - ActionIf popup1 → ajouter action fermer popup1
            - ActionIf popup2 → ajouter action fermer popup2
            - ...
            - ActionVerifierTimeout - Vérifie le timeout
        """
        self.sequence.clear()

        # 1. Lancer BlueStacks (skip si déjà ouvert)
        action_lancer = ListeActions.ActionLancerRaccourci(self)

        # 2. Vérification rapide si déjà prêt (évite l'attente inutile)
        action_verif_rapide = ListeActions.ActionVerifierPretRapide(self)

        # 3. Attendre l'initialisation (seulement si pas déjà prêt)
        action_attendre = ListeActions.ActionAttendre(self, self.temps_initialisation)

        # 3. Boucle de vérification : tant que pas prêt ET pas timeout
        # Condition : le jeu n'est pas encore prêt
        condition_continuer = lambda m: not m.est_jeu_pret() and not m.est_timeout_atteint()

        # Actions dans la boucle
        actions_boucle = [
            # Vérifier si le jeu est prêt
            ListeActions.ActionVerifierPret(self),

            # Vérifier les popups (ActionIf ajoute l'action si condition vraie)
            ListeActions.ActionIf(
                self,
                condition_func=lambda m: m.detect_image("popups/rapport_developpement.png"),
                actions_si_vrai=ListeActions.ActionFermerRapportDeveloppement(self)
            ),
            ListeActions.ActionIf(
                self,
                condition_func=lambda m: m.detect_image("popups/connexion_quotidienne.png"),
                actions_si_vrai=ListeActions.ActionCollecterConnexionQuotidienne(self)
            ),
            ListeActions.ActionIf(
                self,
                condition_func=lambda m: m.detect_image("boutons/bouton_gratuit.png"),
                actions_si_vrai=ListeActions.ActionClicBoutonGratuit(self)
            ),

            # Vérifier le timeout
            ListeActions.ActionVerifierTimeout(self),
        ]

        # Créer la boucle While
        boucle_lancement = ListeActions.ActionWhile(
            self,
            condition_func=condition_continuer,
            actions=actions_boucle,
            max_iterations=1000,  # Sécurité
            nom_boucle="lancement_bluestacks"
        )

        # Ajouter à la séquence optimisée
        self.sequence.add([
            action_lancer,
            action_verif_rapide,  # Vérification rapide pour éviter l'attente si déjà prêt
            action_attendre,
            boucle_lancement,
        ])

        self.logger.debug(
            f"Séquence de lancement: {self.sequence.remaining()} actions"
        )

    def signaler_blocage(self):
        """Appelé par Engine quand trop d'échecs consécutifs"""
        self.logger.warning(f"{self.nom}: Blocage détecté, reboot prévu au prochain tour")
        self._ajouter_historique("BLOCAGE signalé par Engine")
        self._stats['erreurs_detectees'] += 1
        self.etat = EtatBlueStacks.BLOQUE

    def signaler_popup_detecte(self):
        """Appelé quand un popup est détecté pendant le lancement

        Marque qu'un popup a été détecté, ce qui déclenchera un reset
        de la vérification d'icône car le jeu n'est pas encore stable.
        """
        if self._etat == EtatBlueStacks.LANCEMENT:
            self._popup_detecte_pendant_lancement = True
            self._ajouter_historique("Popup détecté pendant lancement")

    def reset_flag_popup(self):
        """Réinitialise le flag de détection de popup"""
        self._popup_detecte_pendant_lancement = False

    def signaler_jeu_charge(self):
        """Appelé par ActionVerifierPret quand le jeu est vraiment prêt (après 2 vérifications)

        Fait la transition vers l'état PRET.
        Casse la boucle ActionWhile en cours.
        """
        if self._etat != EtatBlueStacks.PRET:
            self._ajouter_historique("Jeu chargé et stable - passage en PRET")
            self.etat = EtatBlueStacks.PRET
            self.logger.info(f"{self.nom}: Jeu chargé et prêt !")

            # Casser la boucle de lancement si elle existe
            for loop_id, boucle in list(self.boucles_actives.items()):
                if getattr(boucle, 'nom_boucle', None) == "lancement_bluestacks":
                    boucle.doit_casser = True
                    self.logger.debug("Boucle de lancement interrompue")
                    break

    def signaler_timeout(self):
        """Appelé par ActionVerifierTimeout quand le timeout est atteint

        Sauvegarde l'état et passe en BLOQUE.
        """
        self._ajouter_historique(f"TIMEOUT: {self.TIMEOUT_LANCEMENT // 60} minutes écoulées")
        self.sauvegarder_etat_timeout()
        self.etat = EtatBlueStacks.BLOQUE

        # Casser la boucle de lancement
        for loop_id, boucle in list(self.boucles_actives.items()):
            if getattr(boucle, 'nom_boucle', None) == "lancement_bluestacks":
                boucle.doit_casser = True
                break

    # =========================================================
    # MÉTHODE ABSTRAITE - À implémenter par les sous-classes
    # =========================================================

    @abstractmethod
    def gestion_tour(self):
        """Logique métier du manoir - À implémenter

        Appelée quand le jeu est PRET.
        Doit alimenter la séquence avec les actions à exécuter.
        """
        pass

    def definir_timers(self):
        """Définit les timers - vide par défaut, à surcharger"""
        pass

    def initialiser_sequence(self):
        """Initialise la séquence - vide car gérée par preparer_tour()

        La séquence de lancement est construite dans _construire_sequence_lancement()
        quand l'état passe de NON_LANCE à LANCEMENT.
        """
        pass

    # =========================================================
    # INFORMATIONS
    # =========================================================

    def get_status(self):
        """Retourne le statut du manoir"""
        status = {
            'manoir_id': self.manoir_id,
            'nom': self.nom,
            'etat': self._etat.name,
            'fenetre_ouverte': self.est_fenetre_ouverte(),
            'jeu_charge': self._etat == EtatBlueStacks.PRET,
            'temps_lancement': self.get_temps_depuis_lancement(),
            'titre': self.titre_bluestacks,
        }
        status.update(self._stats)
        return status

    def __repr__(self):
        return f"ManoirBlueStacks('{self.manoir_id}', {self._etat.name})"
