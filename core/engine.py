# -*- coding: utf-8 -*-
"""Moteur principal d'automatisation

Engine est le cœur du système. Il orchestre :
- La rotation entre les fenêtres selon les priorités
- La détection de l'activité utilisateur
- L'exécution des actions
- La persistance de l'état
- Le cycle de vie complet de l'automatisation
"""
import time
import signal
import threading
from enum import Enum, auto
from typing import Dict, Optional, List, Callable

from utils.logger import get_module_logger
from utils.config import (
    PAUSE_ENTRE_ACTIONS,
    PAUSE_ENTRE_FENETRES,
    PAUSE_UTILISATEUR_ACTIF,
    TEMPS_INACTIVITE_REQUIS,
    CONFIG_DIR,
)
from core.simple_scheduler import get_simple_scheduler
from core.message_bus import get_message_bus
from core.user_activity_detector import get_activity_detector
from core.gestionnaire_etats import GestionnaireEtats

logger = get_module_logger("Engine")


class EtatEngine(Enum):
    """États possibles du moteur"""
    ARRETE = auto()
    EN_COURS = auto()
    EN_PAUSE = auto()
    ATTENTE_UTILISATEUR = auto()
    ARRET_EN_COURS = auto()


class Engine:
    """Moteur principal d'automatisation

    Gère le cycle complet d'automatisation multi-manoirs :
    1. Sélection du manoir prioritaire
    2. Activation de la fenêtre
    3. Construction de la séquence selon les timers
    4. Exécution des actions
    5. Vérification des erreurs
    6. Rotation vers le manoir suivant

    Attributes:
        manoirs: Dictionnaire des manoirs gérés
        etat: État actuel du moteur
        stats: Statistiques d'exécution
    """
    
    # Limites de sécurité
    MAX_ECHECS_CONSECUTIFS = 5  # Par manoir
    MAX_ERREURS_CONSECUTIVES = 10  # Global
    MAX_ACTIONS_PAR_MANOIR = 50  # Par tour
    DELAI_ENTRE_VERIFICATIONS = 0.1  # Secondes

    def __init__(self):
        """Initialise le moteur"""
        self.manoirs: Dict[str, 'ManoirBase'] = {}
        self.etat = EtatEngine.ARRETE

        # Composants
        self.scheduler = get_simple_scheduler()
        self.bus = get_message_bus()
        self.activity = get_activity_detector()

        # Gestionnaire d'états (créé au démarrage)
        self._gestionnaire_etats: Optional[GestionnaireEtats] = None

        # État interne
        self._manoir_courant: Optional[str] = None
        self._echecs_consecutifs: Dict[str, int] = {}  # Par manoir
        self._erreurs_consecutives: int = 0  # Global
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()  # Non en pause par défaut

        # Callbacks
        self._on_manoir_change: Optional[Callable] = None
        self._on_action_executed: Optional[Callable] = None
        self._on_error: Optional[Callable] = None
        self._on_state_change: Optional[Callable] = None
        
        # Statistiques (agrégées depuis les manoirs)
        self.stats = {
            'actions_executees': 0,
            'manoirs_traites': 0,
            'erreurs_detectees': 0,
            'temps_total': 0,
            'debut': None,
        }
        
        # Gestion des signaux pour arrêt propre
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        """Configure les gestionnaires de signaux (PROTÉGÉ)"""
        try:
            signal.signal(signal.SIGINT, self._handle_stop_signal)
            signal.signal(signal.SIGTERM, self._handle_stop_signal)
        except (ValueError, OSError):
            # Peut échouer si pas dans le thread principal
            pass
    
    def _handle_stop_signal(self, signum, frame):
        """Gère les signaux d'arrêt (PROTÉGÉ)"""
        logger.info(f"Signal {signum} reçu, arrêt en cours...")
        self.arreter()
    
    # =========================================================
    # CONFIGURATION
    # =========================================================

    def ajouter_manoir(self, manoir):
        """Ajoute un manoir au moteur

        Args:
            manoir: Instance de ManoirBase
        """
        self.manoirs[manoir.manoir_id] = manoir

        # Initialiser le compteur d'échecs
        self._echecs_consecutifs[manoir.manoir_id] = 0

        logger.info(f"Manoir ajouté: {manoir.manoir_id} (priorité={manoir.priorite})")

    def ajouter_manoirs(self, manoirs):
        """Ajoute plusieurs manoirs

        Args:
            manoirs: Dict ou List de manoirs
        """
        if isinstance(manoirs, dict):
            for manoir in manoirs.values():
                self.ajouter_manoir(manoir)
        else:
            for manoir in manoirs:
                self.ajouter_manoir(manoir)

    def set_callback(self, event, callback):
        """Définit un callback pour un événement

        Args:
            event: 'manoir_change', 'action_executed', 'error', 'state_change'
            callback: Fonction à appeler
        """
        if event == 'manoir_change':
            self._on_manoir_change = callback
        elif event == 'action_executed':
            self._on_action_executed = callback
        elif event == 'error':
            self._on_error = callback
        elif event == 'state_change':
            self._on_state_change = callback
    
    # =========================================================
    # CONTRÔLE DU MOTEUR
    # =========================================================
    
    def demarrer(self):
        """Démarre le moteur d'automatisation

        Lance la boucle principale dans le thread courant.
        """
        if self.etat != EtatEngine.ARRETE:
            logger.warning("Moteur déjà démarré")
            return

        if not self.manoirs:
            logger.error("Aucun manoir configuré")
            return

        logger.info("=" * 60)
        logger.info("DÉMARRAGE DU MOTEUR D'AUTOMATISATION")
        logger.info(f"Manoirs: {list(self.manoirs.keys())}")
        logger.info("=" * 60)

        self._changer_etat(EtatEngine.EN_COURS)
        self._stop_event.clear()
        self.stats['debut'] = time.time()

        # Initialiser les manoirs
        self._initialiser_manoirs()

        # Démarrer la détection d'activité
        self.activity.start()

        try:
            self._boucle_principale()
        finally:
            self._cleanup()
    
    def arreter(self):
        """Demande l'arrêt du moteur"""
        if self.etat == EtatEngine.ARRETE:
            return
        
        logger.info("Demande d'arrêt du moteur...")
        self._changer_etat(EtatEngine.ARRET_EN_COURS)
        self._stop_event.set()
    
    def pause(self):
        """Met le moteur en pause"""
        if self.etat == EtatEngine.EN_COURS:
            self._changer_etat(EtatEngine.EN_PAUSE)
            self._pause_event.clear()
            logger.info("Moteur en pause")
    
    def reprendre(self):
        """Reprend après une pause"""
        if self.etat == EtatEngine.EN_PAUSE:
            self._changer_etat(EtatEngine.EN_COURS)
            self._pause_event.set()
            logger.info("Reprise du moteur")
    
    def toggle_pause(self):
        """Bascule l'état de pause"""
        if self.etat == EtatEngine.EN_PAUSE:
            self.reprendre()
        elif self.etat == EtatEngine.EN_COURS:
            self.pause()
    
    def _changer_etat(self, nouvel_etat):
        """Change l'état du moteur (PROTÉGÉ)"""
        ancien_etat = self.etat
        self.etat = nouvel_etat
        
        if self._on_state_change:
            try:
                self._on_state_change(ancien_etat, nouvel_etat)
            except Exception as e:
                logger.error(f"Erreur callback state_change: {e}")
    
    # =========================================================
    # BOUCLE PRINCIPALE
    # =========================================================
    
    def _boucle_principale(self):
        """Boucle principale du moteur (PROTÉGÉ)"""
        logger.info("Boucle principale démarrée")
        
        while not self._stop_event.is_set():
            try:
                # Attendre si en pause
                if not self._pause_event.wait(timeout=0.5):
                    continue
                
                # Vérifier l'activité utilisateur
                if not self._attendre_inactivite():
                    continue
                
                # Nettoyer les messages expirés
                self.bus.clear_expired()

                # Sélectionner le manoir prioritaire via le scheduler
                selection = self.scheduler.selectionner_manoir(self.manoirs)

                if not selection:
                    # Aucun manoir disponible, attendre
                    temps_attente = self.scheduler.get_temps_attente(self.manoirs)
                    if temps_attente and temps_attente > 0:
                        attente = min(temps_attente, 30)  # Max 30s
                        logger.debug(f"Aucun manoir disponible, attente {attente:.1f}s")
                        self._attendre_interruptible(attente)
                    else:
                        self._attendre_interruptible(5)
                    continue

                # Si le manoir n'est pas prêt, attendre
                if not selection.pret:
                    attente = min(selection.temps_avant_passage, 30)
                    logger.debug(f"Prochain manoir dans {attente:.1f}s")
                    self._attendre_interruptible(attente)
                    continue

                # Traiter le manoir sélectionné
                manoir_id = selection.manoir_id

                if manoir_id != self._manoir_courant:
                    self._changer_manoir(manoir_id)

                # Exécuter le tour pour ce manoir
                self._executer_tour_manoir(manoir_id)

                # Pause entre manoirs
                self._attendre_interruptible(PAUSE_ENTRE_FENETRES)
                
            except Exception as e:
                logger.error(f"Erreur boucle principale: {e}")
                self._erreurs_consecutives += 1
                
                if self._erreurs_consecutives >= self.MAX_ERREURS_CONSECUTIVES:
                    logger.critical("Trop d'erreurs consécutives, arrêt")
                    break
                
                time.sleep(1)
        
        logger.info("Boucle principale terminée")
    
    def _attendre_inactivite(self):
        """Attend que l'utilisateur soit inactif (PROTÉGÉ)
        
        Returns:
            bool: True si on peut continuer, False si arrêt demandé
        """
        if self.activity.is_user_active(TEMPS_INACTIVITE_REQUIS):
            if self.etat != EtatEngine.ATTENTE_UTILISATEUR:
                self._changer_etat(EtatEngine.ATTENTE_UTILISATEUR)
                logger.info("Utilisateur actif, en attente...")
            
            # Attendre l'inactivité
            while not self._stop_event.is_set():
                if self.activity.wait_for_inactivity(TEMPS_INACTIVITE_REQUIS, max_wait=1):
                    break
            
            if self._stop_event.is_set():
                return False
            
            self._changer_etat(EtatEngine.EN_COURS)
            logger.info("Utilisateur inactif, reprise")
        
        return True
    
    def _attendre_interruptible(self, duree):
        """Attend une durée, interruptible par stop (PROTÉGÉ)"""
        self._stop_event.wait(timeout=duree)
    
    # =========================================================
    # GESTION DES MANOIRS
    # =========================================================

    def _initialiser_manoirs(self):
        """Initialise tous les manoirs (PROTÉGÉ)"""
        # Créer le gestionnaire d'états partagé
        try:
            chemin_config = CONFIG_DIR / "etat-chemin.toml"
            self._gestionnaire_etats = GestionnaireEtats(str(chemin_config))
            logger.info("Gestionnaire d'états créé")
        except Exception as e:
            logger.warning(f"Gestionnaire d'états non disponible: {e}")
            self._gestionnaire_etats = None

        for manoir_id, manoir in self.manoirs.items():
            try:
                # Injecter le gestionnaire d'états
                if self._gestionnaire_etats:
                    manoir.set_gestionnaire(self._gestionnaire_etats)

                # Définir les timers
                manoir.definir_timers()

                # Initialiser la séquence
                manoir.initialiser_sequence()

                logger.info(f"Manoir {manoir_id} initialisé")

            except Exception as e:
                logger.error(f"Erreur initialisation {manoir_id}: {e}")

    def _changer_manoir(self, manoir_id):
        """Change le manoir courant (PROTÉGÉ)"""
        self._manoir_courant = manoir_id
        manoir = self.manoirs[manoir_id]

        logger.info(f"Changement vers manoir: {manoir.nom}")

        # Callback
        if self._on_manoir_change:
            try:
                self._on_manoir_change(manoir_id, manoir)
            except Exception as e:
                logger.error(f"Erreur callback manoir_change: {e}")

        self.stats['manoirs_traites'] += 1

    def _executer_tour_manoir(self, manoir_id):
        """Exécute un tour pour un manoir (PROTÉGÉ)

        1. Appelle manoir.preparer_tour() qui alimente la séquence
        2. Exécute les actions de la séquence
        3. Compte les échecs et signale le blocage si nécessaire

        Args:
            manoir_id: ID du manoir
        """
        manoir = self.manoirs[manoir_id]

        # Manoir prépare et alimente sa séquence
        try:
            pret = manoir.preparer_tour()
        except Exception as e:
            logger.error(f"Erreur preparer_tour {manoir_id}: {e}")
            return

        if not pret:
            logger.debug(f"{manoir_id}: Pas prêt (en cours de lancement/chargement)")
            return

        if manoir.sequence.is_end():
            logger.debug(f"{manoir_id}: Aucune action à exécuter")
            return

        # Exécuter les actions de la séquence
        actions_executees = 0

        while not manoir.sequence.is_end() and not self._stop_event.is_set():
            # Limite de sécurité
            if actions_executees >= self.MAX_ACTIONS_PAR_MANOIR:
                logger.warning(f"{manoir_id}: Limite d'actions atteinte")
                break

            # Vérifier l'activité utilisateur
            if self.activity.is_user_active(1):
                logger.info("Activité utilisateur détectée, pause")
                break

            # Récupérer l'action courante
            try:
                action = next(manoir.sequence)
            except StopIteration:
                break

            # Exécuter l'action
            try:
                if action and action.condition():
                    nom = getattr(action, 'nom', action.__class__.__name__)
                    logger.debug(f"Exécution: {nom}")

                    result = action.execute()

                    # VÉRIFIER SI REPRISE PREPARER_TOUR DEMANDÉE (chemin incertain)
                    if getattr(action, 'demande_reprise', False):
                        logger.debug(f"{manoir_id}: Reprise preparer_tour demandée")
                        if result:
                            actions_executees += 1
                            self.stats['actions_executees'] += 1
                            self._echecs_consecutifs[manoir_id] = 0
                            manoir.incrementer_stat('actions_executees')
                        # Rappeler preparer_tour pour recalculer le chemin
                        try:
                            manoir.preparer_tour()
                        except Exception as e:
                            logger.error(f"Erreur reprise preparer_tour: {e}")
                        continue  # Continuer avec la nouvelle séquence

                    # VÉRIFIER SI ROTATION DEMANDÉE (attente non bloquante)
                    if manoir.doit_tourner():
                        logger.debug(f"{manoir_id}: Rotation demandée par action")
                        if result:
                            actions_executees += 1
                            self.stats['actions_executees'] += 1
                            self._echecs_consecutifs[manoir_id] = 0
                            manoir.incrementer_stat('actions_executees')
                        break  # Sortir, passer au manoir suivant

                    if result:
                        # Succès
                        actions_executees += 1
                        self.stats['actions_executees'] += 1
                        self._echecs_consecutifs[manoir_id] = 0
                        manoir.incrementer_stat('actions_executees')

                        # Callback
                        if self._on_action_executed:
                            try:
                                self._on_action_executed(manoir_id, actions_executees)
                            except Exception:
                                pass
                    else:
                        # Échec - condition non remplie
                        self._echecs_consecutifs[manoir_id] += 1
                        manoir.incrementer_stat('actions_echouees')
                        logger.debug(f"Action {nom} échouée (condition non remplie)")

                        # Vérifier si blocage
                        if self._echecs_consecutifs[manoir_id] >= self.MAX_ECHECS_CONSECUTIFS:
                            logger.warning(f"{manoir_id}: {self.MAX_ECHECS_CONSECUTIFS} échecs consécutifs - signalement blocage")
                            manoir.signaler_blocage()
                            break
                else:
                    # Action ignorée (condition fausse)
                    nom = getattr(action, 'nom', action.__class__.__name__) if action else 'None'
                    logger.debug(f"Action ignorée: {nom}")

            except Exception as e:
                logger.error(f"Erreur exécution action: {e}")
                self._echecs_consecutifs[manoir_id] += 1

                if self._on_error:
                    try:
                        self._on_error(manoir_id, str(e))
                    except Exception:
                        pass

            # Pause entre actions
            time.sleep(PAUSE_ENTRE_ACTIONS)

        logger.debug(f"{manoir_id}: {actions_executees} actions exécutées")
    
    # =========================================================
    # NETTOYAGE
    # =========================================================
    
    def _cleanup(self):
        """Nettoie les ressources (PROTÉGÉ)"""
        logger.info("Nettoyage en cours...")

        # Arrêter la détection d'activité
        self.activity.stop()

        # Calculer les statistiques finales (agréger depuis les manoirs)
        if self.stats['debut']:
            self.stats['temps_total'] = time.time() - self.stats['debut']

        # Agréger les erreurs depuis les manoirs
        total_erreurs = 0
        for manoir in self.manoirs.values():
            stats_manoir = manoir.get_stats()
            total_erreurs += stats_manoir.get('erreurs_detectees', 0)
        self.stats['erreurs_detectees'] = total_erreurs

        self._changer_etat(EtatEngine.ARRETE)

        # Afficher le résumé
        logger.info("=" * 60)
        logger.info("ARRÊT DU MOTEUR")
        logger.info(f"Actions exécutées: {self.stats['actions_executees']}")
        logger.info(f"Manoirs traités: {self.stats['manoirs_traites']}")
        logger.info(f"Erreurs détectées: {self.stats['erreurs_detectees']}")
        if self.stats['temps_total'] > 0:
            logger.info(f"Durée totale: {self.stats['temps_total']:.1f}s")
        logger.info("=" * 60)
    
    # =========================================================
    # INFORMATIONS
    # =========================================================
    
    def get_stats(self):
        """Retourne les statistiques actuelles (agrégées depuis les manoirs)

        Returns:
            dict: Statistiques
        """
        stats = self.stats.copy()
        if stats['debut']:
            stats['temps_ecoule'] = time.time() - stats['debut']

        # Agréger les stats des manoirs
        stats['par_manoir'] = {}
        total_erreurs = 0
        for manoir_id, manoir in self.manoirs.items():
            stats_manoir = manoir.get_stats()
            stats['par_manoir'][manoir_id] = stats_manoir
            total_erreurs += stats_manoir.get('erreurs_detectees', 0)

        stats['erreurs_detectees'] = total_erreurs
        return stats

    def get_status(self):
        """Retourne le statut actuel du moteur

        Returns:
            dict: Statut
        """
        return {
            'etat': self.etat.name,
            'manoir_courant': self._manoir_courant,
            'nb_manoirs': len(self.manoirs),
            'erreurs_consecutives': self._erreurs_consecutives,
        }

    def __repr__(self):
        return f"Engine(état={self.etat.name}, manoirs={len(self.manoirs)})"


# Instance globale
_engine_instance = None


def get_engine():
    """Retourne l'instance singleton du moteur
    
    Returns:
        Engine: Instance partagée
    """
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = Engine()
    return _engine_instance
