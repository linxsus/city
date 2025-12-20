# -*- coding: utf-8 -*-
"""Classe abstraite de base pour les manoirs

ManoirBase définit l'interface commune pour tous les manoirs
(principal et farms). Elle gère :
- La séquence d'actions
- La détection visuelle
- Les interactions (clics, saisie)
- La gestion des erreurs
- L'état et les variables
"""
import time
from abc import ABC, abstractmethod
from pathlib import Path

from utils.config import (
    DEFAULT_IMAGE_THRESHOLD,
    CAPTURES_DIR,
    TEMPLATES_DIR,
)
from manoirs.config_manoirs import (
    BLUESTACKS_LARGEUR_ZONE_JEU,
    BLUESTACKS_LARGEUR_BANDEAU,
    BLUESTACKS_LARGEUR_ZONE_AVEC_BANDEAU,
    BLUESTACKS_SEUIL_RATIO_PUB,
)
from utils.logger import get_manoir_logger
from utils.coordinates import relative_to_absolute, clamp_to_window
import actions.liste_actions as ListeActions
from vision.screen_capture import get_screen_capture
from vision.image_matcher import get_image_matcher
from vision.color_detector import get_color_detector
from vision.ocr_engine import get_ocr_engine
from core.window_manager import get_window_manager
from core.slot_manager import get_slot_manager
from core.timer_manager import get_timer_manager
from core.window_state_manager import get_window_state_manager
from core.message_bus import get_message_bus


class ManoirBase(ABC):
    """Classe abstraite de base pour un manoir d'automatisation

    Attributes:
        manoir_id: Identifiant unique du manoir
        nom: Nom affichable
        titre_bluestacks: Titre de la fenêtre BlueStacks
        largeur: Largeur de la zone de jeu (zone de référence pour positionnement)
        hauteur: Hauteur de la zone de jeu
        priorite: Priorité statique (0-100)
        slots_config: Configuration des slots [{'nom': str, 'nb': int}, ...]
    """

    # Configuration de slots par défaut
    DEFAULT_SLOTS_CONFIG = [{'nom': 'default', 'nb': 3}]

    def __init__(self, manoir_id, nom=None, titre_bluestacks=None,
                 largeur=1280, hauteur=720, priorite=50, slots_config=None,
                 position_x=None, position_y=None):
        """
        Args:
            manoir_id: Identifiant unique
            nom: Nom affichable (défaut = manoir_id)
            titre_bluestacks: Titre de la fenêtre BlueStacks
            largeur: Largeur de la zone de jeu (zone de référence)
            hauteur: Hauteur de la zone de jeu
            priorite: Priorité (0-100)
            slots_config: Configuration des slots [{'nom': str, 'nb': int}, ...]
            position_x: Position X de la fenêtre (None pour ne pas déplacer)
            position_y: Position Y de la fenêtre (None pour ne pas déplacer)
        """
        self.manoir_id = manoir_id
        self.nom = nom or manoir_id
        self.titre_bluestacks = titre_bluestacks or manoir_id
        self.largeur = largeur
        self.hauteur = hauteur
        self.priorite = priorite
        self.slots_config = slots_config or self.DEFAULT_SLOTS_CONFIG
        self.position_x = position_x
        self.position_y = position_y
        
        # Logger dédié (utilise le nom lisible pour les logs console)
        self.logger = get_manoir_logger(self.nom)
        
        # Séquence d'actions (alimentée par preparer_tour)
        self.sequence = ListeActions.SequenceActions()
        
        # Listes de slots (triées par prochain_disponible)
        self.slots_prioritaires = []  # slots urgents (popups, erreurs...)
        self.slots_normaux = []       # slots standards (mercenaires, construction...)
        
        # État
        self.termine = False
        self.variables = {}
        self.boucles_actives = {}
        self._etats_boucles = {}
        
        # Handle de la fenêtre Windows
        self._hwnd = None
        self._rect = None

        # Dimensions et position attendues (pour détecter les changements)
        self._position_attendue = None  # (x, y, width, height)
        self._fenetre_placee = False     # True après le premier placement

        # Dernière capture d'écran (cache)
        self._derniere_capture = None
        self._capture_timestamp = 0
        self._capture_ttl = 0.5  # Durée de validité du cache
        
        # Managers (accès via singletons)
        self._wm = get_window_manager()
        self._sm = get_slot_manager()
        self._tm = get_timer_manager()
        self._wsm = get_window_state_manager()
        self._bus = get_message_bus()
        
        # Vision
        self._screen = get_screen_capture()
        self._matcher = get_image_matcher()
        self._color = get_color_detector()
        self._ocr = get_ocr_engine()
        
        # Statistiques locales
        self._stats = {
            'actions_executees': 0,
            'actions_echouees': 0,
            'erreurs_detectees': 0,
            'temps_actif': 0,
            'derniere_activite': None,
        }
        
        # Mécanisme d'attente non bloquante
        self._demande_rotation = False
        
        # Enregistrer auprès des managers
        self._register()
    
    def _register(self):
        """Enregistre le manoir auprès des managers (PROTÉGÉ)"""
        self._wsm.register_manoir(self.manoir_id)
        self._sm.register_manoir(self.manoir_id, self.slots_config)
        slots_str = ', '.join(f"{s['nom']}:{s['nb']}" for s in self.slots_config)
        self.logger.info(f"Manoir {self.nom} enregistré (slots: {slots_str})")
    
    # =========================================================
    # GESTION DE LA FENÊTRE WINDOWS
    # =========================================================
    
    def find_window(self):
        """Trouve la fenêtre BlueStacks
        
        Returns:
            int ou None: Handle de la fenêtre
        """
        self._hwnd = self._wm.find_window(self.titre_bluestacks)
        if self._hwnd:
            self._rect = self._wm.get_window_rect(self._hwnd)
        return self._hwnd
    
    def activate(self):
        """Active la fenêtre (met au premier plan)

        Vérifie aussi si la fenêtre a été déplacée/redimensionnée et la replace si nécessaire.

        Returns:
            bool: True si succès
        """
        if not self._hwnd:
            self.find_window()

        if self._hwnd:
            # Vérifier et replacer la fenêtre si elle a été déplacée/redimensionnée
            if self.position_x is not None or self.position_y is not None:
                self.placer_fenetre()

            return self._wm.activate_window(self._hwnd)

        self.logger.warning(f"Fenêtre {self.titre_bluestacks} non trouvée")
        return False

    def placer_fenetre(self):
        """Place la fenêtre à la position et dimensions configurées

        Gère automatiquement les fenêtres BlueStacks avec ou sans publicité.

        Structure de la fenêtre BlueStacks (de gauche à droite):
        [PUB (~320px)] [ZONE DE JEU (~563px)] [BANDEAU DROIT (~32px)]

        La pub est à gauche, donc on décale la fenêtre vers la gauche pour
        que la zone de jeu soit visible à la position configurée.

        Returns:
            bool: True si succès
        """
        if not self._hwnd:
            self.find_window()

        if not self._hwnd:
            self.logger.warning(f"Impossible de placer: fenêtre {self.titre_bluestacks} non trouvée")
            return False

        # Récupérer les dimensions actuelles AVANT redimensionnement
        rect_actuelle = self._wm.get_window_rect(self._hwnd)
        if not rect_actuelle:
            self.logger.error("Impossible de récupérer la position actuelle")
            return False

        x_actuel, y_actuel = rect_actuelle[0], rect_actuelle[1]
        largeur_actuelle = rect_actuelle[2] - rect_actuelle[0]
        hauteur_actuelle = rect_actuelle[3] - rect_actuelle[1]

        # Calculer le ratio actuel pour détecter la présence de pub
        ratio_actuel = largeur_actuelle / hauteur_actuelle if hauteur_actuelle > 0 else 0
        a_pub = ratio_actuel > BLUESTACKS_SEUIL_RATIO_PUB

        # Détecter si bandeau présent (tolérance de 20px)
        # Sans pub : 563 (sans bandeau) ou 595 (avec bandeau)
        # Avec pub : 883 (sans bandeau) ou 915 (avec bandeau)
        largeur_base = largeur_actuelle
        if a_pub:
            # Soustraire la pub estimée pour obtenir la zone de jeu
            largeur_base = largeur_actuelle - (largeur_actuelle - BLUESTACKS_LARGEUR_ZONE_AVEC_BANDEAU)

        a_bandeau = abs(largeur_base - BLUESTACKS_LARGEUR_ZONE_AVEC_BANDEAU) < 20 or \
                    abs(largeur_actuelle - BLUESTACKS_LARGEUR_ZONE_AVEC_BANDEAU) < 20

        if not self._fenetre_placee:
            self.logger.info(
                f"Premier placement - Dimensions: {largeur_actuelle}x{hauteur_actuelle}, "
                f"ratio: {ratio_actuel:.3f}, pub: {a_pub}, bandeau: {a_bandeau}"
            )

        # Si déjà placée, vérifier si elle a été modifiée
        if self._fenetre_placee and self._position_attendue:
            x_att, y_att, w_att, h_att = self._position_attendue
            tolerance = 5

            if (abs(x_actuel - x_att) <= tolerance and
                abs(y_actuel - y_att) <= tolerance and
                abs(largeur_actuelle - w_att) <= tolerance and
                abs(hauteur_actuelle - h_att) <= tolerance):
                return True
            else:
                self.logger.info(
                    f"Fenêtre modifiée: ({x_actuel}, {y_actuel}, {largeur_actuelle}x{hauteur_actuelle}) != "
                    f"attendu ({x_att}, {y_att}, {w_att}x{h_att})"
                )

        # Redimensionner avec maintien du ratio actuel
        success = self._wm.resize_with_aspect_ratio(
            self._hwnd,
            height=self.hauteur,
            aspect_ratio=None,  # Garde le ratio actuel (avec ou sans pub)
            x=self.position_x,
            y=self.position_y
        )

        if not success:
            return False

        # Récupérer la largeur réelle après redimensionnement
        size = self._wm.get_window_size(self._hwnd)
        if not size:
            self.logger.error("Impossible de récupérer les dimensions après redimensionnement")
            return False

        largeur_calculee, hauteur_reelle = size

        # Recalculer la détection pub/bandeau après redimensionnement
        ratio_apres = largeur_calculee / hauteur_reelle if hauteur_reelle > 0 else 0
        a_pub_apres = ratio_apres > BLUESTACKS_SEUIL_RATIO_PUB

        # Calculer la largeur de la zone de jeu (avec ou sans bandeau)
        # En utilisant les constantes de config_manoirs
        if a_pub_apres:
            # Avec pub : largeur_pub = largeur_totale - zone_jeu_avec_bandeau
            largeur_pub = largeur_calculee - BLUESTACKS_LARGEUR_ZONE_AVEC_BANDEAU
            largeur_zone_jeu = BLUESTACKS_LARGEUR_ZONE_AVEC_BANDEAU
        else:
            # Sans pub : la fenêtre EST la zone de jeu (avec ou sans bandeau)
            largeur_pub = 0
            largeur_zone_jeu = largeur_calculee

        # Calculer la position finale
        position_x_base = self.position_x if self.position_x is not None else 0
        position_y_finale = self.position_y if self.position_y is not None else 0

        # Décaler vers la gauche pour cacher la pub
        # La zone de jeu doit commencer à position_x_base
        position_x_finale = position_x_base - largeur_pub

        self.logger.info(
            f"Calcul position: largeur_totale={largeur_calculee}, largeur_pub={largeur_pub}, "
            f"largeur_zone_jeu={largeur_zone_jeu}"
        )

        if largeur_pub > 0:
            self.logger.info(
                f"Pub présente ({largeur_pub}px) - Décalage vers la gauche "
                f"(x: {position_x_base} -> {position_x_finale})"
            )

        # Repositionner la fenêtre
        self._wm.move_and_resize_window(
            self._hwnd,
            x=position_x_finale,
            y=position_y_finale,
            width=largeur_calculee,
            height=hauteur_reelle
        )

        # Mémoriser la position attendue pour détecter les changements
        self._position_attendue = (position_x_finale, position_y_finale, largeur_calculee, hauteur_reelle)
        self._fenetre_placee = True

        self.logger.info(
            f"Fenêtre placée: position ({position_x_finale}, {position_y_finale}), "
            f"dimensions {largeur_calculee}x{hauteur_reelle}, zone_jeu visible à x={position_x_base}"
        )

        return True
    
    def is_valid(self):
        """Vérifie si la fenêtre est valide et visible
        
        Returns:
            bool: True si valide
        """
        if not self._hwnd:
            self.find_window()
        
        if self._hwnd:
            return self._wm.is_window_visible(self._hwnd)
        return False
    
    def get_rect(self):
        """Retourne les coordonnées de la fenêtre
        
        Returns:
            Tuple (left, top, right, bottom) ou None
        """
        if not self._rect or not self._hwnd:
            self.find_window()
        return self._rect
    
    # =========================================================
    # CAPTURE D'ÉCRAN
    # =========================================================
    
    def capture(self, force=False):
        """Capture l'écran de la fenêtre
        
        Args:
            force: Forcer une nouvelle capture même si cache valide
            
        Returns:
            PIL.Image ou None
        """
        now = time.time()
        
        # Utiliser le cache si valide
        if not force and self._derniere_capture:
            if (now - self._capture_timestamp) < self._capture_ttl:
                return self._derniere_capture
        
        # Obtenir les coordonnées de la fenêtre
        rect = self.get_rect()
        if not rect:
            self.logger.error("Impossible de capturer: fenêtre non trouvée")
            return None
        
        try:
            # Capturer la région de la fenêtre
            image = self._screen.capture_window_region(rect)
            
            self._derniere_capture = image
            self._capture_timestamp = now
            
            return image
            
        except Exception as e:
            self.logger.error(f"Erreur capture: {e}")
            return None
    
    def save_capture(self, suffix=""):
        """Sauvegarde la capture courante
        
        Args:
            suffix: Suffixe pour le nom de fichier
            
        Returns:
            Path ou None: Chemin du fichier sauvegardé
        """
        image = self.capture()
        if not image:
            return None
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{self.manoir_id}_{timestamp}{suffix}.png"
        filepath = CAPTURES_DIR / filename
        
        try:
            self._screen.save_capture(image, str(filepath))
            self.logger.debug(f"Capture sauvegardée: {filepath}")
            return filepath
        except Exception as e:
            self.logger.error(f"Erreur sauvegarde capture: {e}")
            return None
    
    def invalidate_capture(self):
        """Invalide le cache de capture"""
        self._derniere_capture = None
        self._capture_timestamp = 0
    
    # =========================================================
    # DÉTECTION VISUELLE
    # =========================================================
    
    def detect_image(self, template_path, threshold=None, region=None):
        """Détecte si une image template est présente
        
        Args:
            template_path: Chemin vers l'image template
            threshold: Seuil de confiance (0-1)
            region: Région de recherche (x, y, w, h) optionnelle
            
        Returns:
            bool: True si trouvée
        """
        return self.find_image(template_path, threshold, region) is not None
    
    def find_image(self, template_path, threshold=None, region=None):
        """Trouve une image template et retourne sa position

        Args:
            template_path: Chemin vers l'image template
            threshold: Seuil de confiance (0-1)
            region: Région de recherche optionnelle

        Returns:
            Tuple (x, y) ou None
        """
        if threshold is None:
            threshold = DEFAULT_IMAGE_THRESHOLD

        # Résoudre le chemin
        template_path = self._resolve_template_path(template_path)

        image = self.capture()
        if not image:
            return None

        # Extraire la région si spécifiée
        if region:
            x, y, w, h = region
            image = image.crop((x, y, x + w, y + h))
            offset_x, offset_y = x, y
        else:
            offset_x, offset_y = 0, 0

        result = self._matcher.find_template(image, template_path, threshold)

        if result:
            x, y, confidence = result
            return (x + offset_x, y + offset_y)

        return None

    def find_image_multiscale(self, template_path, threshold=None, region=None, scales=None):
        """Trouve une image template à plusieurs échelles

        Utile quand le template peut avoir une résolution différente de l'écran.

        Args:
            template_path: Chemin vers l'image template
            threshold: Seuil de confiance (0-1)
            region: Région de recherche optionnelle
            scales: Liste d'échelles à tester (défaut: [0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3])

        Returns:
            Tuple (x, y) ou None
        """
        if threshold is None:
            threshold = DEFAULT_IMAGE_THRESHOLD

        # Résoudre le chemin
        template_path = self._resolve_template_path(template_path)

        image = self.capture()
        if not image:
            return None

        # Extraire la région si spécifiée
        if region:
            x, y, w, h = region
            image = image.crop((x, y, x + w, y + h))
            offset_x, offset_y = x, y
        else:
            offset_x, offset_y = 0, 0

        result = self._matcher.find_template_multiscale(image, template_path, threshold, scales)

        if result:
            x, y, confidence = result[:3]
            return (x + offset_x, y + offset_y)

        return None

    def detect_image_multiscale(self, template_path, threshold=None, region=None, scales=None):
        """Détecte si une image template est présente (multi-échelle)

        Args:
            template_path: Chemin vers l'image template
            threshold: Seuil de confiance (0-1)
            region: Région de recherche optionnelle
            scales: Liste d'échelles à tester

        Returns:
            bool: True si trouvée
        """
        return self.find_image_multiscale(template_path, threshold, region, scales) is not None
    
    def find_all_images(self, template_path, threshold=None, region=None, min_distance=10):
        """Trouve toutes les occurrences d'une image
        
        Args:
            template_path: Chemin vers l'image template
            threshold: Seuil de confiance
            region: Région de recherche optionnelle
            min_distance: Distance minimale entre résultats
            
        Returns:
            List[(x, y)]: Positions trouvées
        """
        if threshold is None:
            threshold = DEFAULT_IMAGE_THRESHOLD
        
        template_path = self._resolve_template_path(template_path)
        
        image = self.capture()
        if not image:
            return []
        
        if region:
            x, y, w, h = region
            image = image.crop((x, y, x + w, y + h))
            offset_x, offset_y = x, y
        else:
            offset_x, offset_y = 0, 0
        
        results = self._matcher.find_all_templates(
            image, template_path, threshold, min_distance
        )
        
        return [(r[0] + offset_x, r[1] + offset_y) for r in results]
    
    def detect_text(self, search_text, region=None, case_sensitive=False):
        """Détecte si un texte est présent (OCR)
        
        Args:
            search_text: Texte à chercher
            region: Région de recherche optionnelle
            case_sensitive: Sensible à la casse
            
        Returns:
            bool: True si trouvé
        """
        image = self.capture()
        if not image:
            return False
        
        if region:
            x, y, w, h = region
            image = image.crop((x, y, x + w, y + h))
        
        return self._ocr.find_text(image, search_text, case_sensitive=case_sensitive)
    
    def find_text(self, search_text, region=None, case_sensitive=False):
        """Trouve un texte et retourne sa position
        
        Args:
            search_text: Texte à chercher
            region: Région de recherche optionnelle
            case_sensitive: Sensible à la casse
            
        Returns:
            Tuple (x, y) ou None
        """
        image = self.capture()
        if not image:
            return None
        
        if region:
            x, y, w, h = region
            image = image.crop((x, y, x + w, y + h))
            offset_x, offset_y = x, y
        else:
            offset_x, offset_y = 0, 0
        
        result = self._ocr.find_text_position(
            image, search_text, case_sensitive=case_sensitive
        )
        
        if result:
            return (result[0] + offset_x, result[1] + offset_y)
        
        return None
    
    def extract_text(self, region=None):
        """Extrait le texte d'une région (OCR)
        
        Args:
            region: Région à analyser (x, y, w, h)
            
        Returns:
            str: Texte extrait
        """
        image = self.capture()
        if not image:
            return ""
        
        if region:
            x, y, w, h = region
            image = image.crop((x, y, x + w, y + h))
        
        return self._ocr.extract_text(image)
    
    def check_color_at(self, x, y, expected_rgb, tolerance=10):
        """Vérifie la couleur à une position
        
        Args:
            x, y: Position du pixel
            expected_rgb: Couleur attendue (r, g, b)
            tolerance: Tolérance par composante
            
        Returns:
            bool: True si couleur correspond
        """
        image = self.capture()
        if not image:
            return False
        
        return self._color.check_color_at(image, x, y, expected_rgb, tolerance)
    
    def get_color_at(self, x, y):
        """Récupère la couleur à une position
        
        Args:
            x, y: Position du pixel
            
        Returns:
            Tuple (r, g, b) ou None
        """
        image = self.capture()
        if not image:
            return None
        
        return self._color.get_color_at(image, x, y)
    
    def _resolve_template_path(self, path):
        """Résout le chemin d'un template (PROTÉGÉ)"""
        path = Path(path)
        if path.is_absolute():
            return str(path)
        
        # Essayer dans templates/
        full_path = TEMPLATES_DIR / path
        if full_path.exists():
            return str(full_path)
        
        return str(path)
    
    # =========================================================
    # INTERACTIONS
    # =========================================================
    
    def click_at(self, x, y, relative=False):
        """Effectue un clic à une position
        
        Args:
            x, y: Position du clic
            relative: Si True, coordonnées relatives (0-1)
        """
        if relative:
            x, y = relative_to_absolute(x, y, self.largeur, self.hauteur)

        # Contraindre aux limites (window_rect = (0, 0, largeur, hauteur))
        window_rect = (0, 0, self.largeur, self.hauteur)
        x, y = clamp_to_window(x, y, window_rect)
        
        # Convertir en coordonnées écran
        rect = self.get_rect()
        if not rect:
            self.logger.error("Impossible de cliquer: fenêtre non trouvée")
            return
        
        screen_x = rect[0] + x
        screen_y = rect[1] + y
        
        self._perform_click(screen_x, screen_y)
        self.logger.debug(f"Clic à ({x}, {y}) -> écran ({screen_x}, {screen_y})")
        
        # Invalider le cache de capture
        self.invalidate_capture()
    
    def click_image(self, template_path, threshold=None, offset=(0, 0)):
        """Clique sur une image si trouvée
        
        Args:
            template_path: Chemin vers l'image template
            threshold: Seuil de confiance
            offset: Décalage (dx, dy) par rapport au centre
            
        Returns:
            bool: True si cliqué
        """
        pos = self.find_image(template_path, threshold)
        if pos:
            x, y = pos
            self.click_at(x + offset[0], y + offset[1])
            return True
        return False
    
    def click_text(self, search_text, region=None, offset=(0, 0)):
        """Clique sur un texte si trouvé
        
        Args:
            search_text: Texte à chercher
            region: Région de recherche
            offset: Décalage par rapport au centre
            
        Returns:
            bool: True si cliqué
        """
        pos = self.find_text(search_text, region)
        if pos:
            x, y = pos
            self.click_at(x + offset[0], y + offset[1])
            return True
        return False
    
    def _perform_click(self, screen_x, screen_y):
        """Effectue le clic physique (PROTÉGÉ)
        
        À surcharger si nécessaire pour utiliser différentes méthodes.
        """
        try:
            import pyautogui
            pyautogui.click(screen_x, screen_y)
        except ImportError:
            self.logger.error("pyautogui non disponible pour les clics")
    
    def type_text(self, text, interval=0.05):
        """Saisit du texte
        
        Args:
            text: Texte à saisir
            interval: Intervalle entre les caractères
        """
        try:
            import pyautogui
            pyautogui.typewrite(text, interval=interval)
            self.invalidate_capture()
        except ImportError:
            self.logger.error("pyautogui non disponible pour la saisie")
    
    def press_key(self, key):
        """Appuie sur une touche
        
        Args:
            key: Touche à presser (ex: 'enter', 'escape')
        """
        try:
            import pyautogui
            pyautogui.press(key)
            self.invalidate_capture()
        except ImportError:
            self.logger.error("pyautogui non disponible pour les touches")
    
    # =========================================================
    # VARIABLES ET ÉTAT
    # =========================================================
    
    def get_variable(self, nom, default=None):
        """Récupère une variable
        
        Args:
            nom: Nom de la variable
            default: Valeur par défaut
            
        Returns:
            Valeur de la variable
        """
        return self.variables.get(nom, default)
    
    def set_variable(self, nom, valeur):
        """Définit une variable
        
        Args:
            nom: Nom de la variable
            valeur: Valeur à définir
        """
        self.variables[nom] = valeur
    
    def increment_variable(self, nom, increment=1):
        """Incrémente une variable numérique
        
        Args:
            nom: Nom de la variable
            increment: Valeur d'incrément
            
        Returns:
            Nouvelle valeur
        """
        current = self.variables.get(nom, 0)
        new_value = current + increment
        self.variables[nom] = new_value
        return new_value
    
    # =========================================================
    # SLOTS ET TIMERS
    # =========================================================
    
    def has_free_slot(self):
        """Vérifie si un slot est disponible

        Returns:
            bool: True si au moins un slot libre
        """
        return self._sm.has_free_slot(self.manoir_id)

    def count_free_slots(self):
        """Compte les slots libres

        Returns:
            int: Nombre de slots libres
        """
        return self._sm.count_free_slots(self.manoir_id)

    def occupy_slot(self, duree=None, type_action=None):
        """Occupe un slot

        Args:
            duree: Durée estimée en secondes
            type_action: Type d'action

        Returns:
            Slot ou None
        """
        return self._sm.occupy_slot(self.manoir_id, duree, type_action)

    def get_due_timers(self):
        """Récupère les timers dus pour ce manoir

        Returns:
            List[Timer]: Timers à exécuter
        """
        return self._tm.get_due_timers(self.manoir_id)

    def mark_timer_executed(self, timer_nom):
        """Marque un timer comme exécuté

        Args:
            timer_nom: Nom du timer
        """
        self._tm.mark_executed(timer_nom, self.manoir_id)
        
        
    
    # =========================================================
    # MÉTHODES ABSTRAITES
    # =========================================================
    
    @abstractmethod
    def preparer_tour(self):
        """Prépare le tour et alimente la séquence
        
        À implémenter dans les sous-classes.
        Doit gérer:
        - L'état de la fenêtre (lancement, chargement, blocage)
        - L'alimentation de la séquence selon les timers
        
        Returns:
            bool: True si prêt à exécuter, False sinon
        """
        pass
    
    @abstractmethod
    def definir_timers(self):
        """Définit les timers pour cette fenêtre
        
        À implémenter dans les sous-classes.
        """
        pass
    
    # =========================================================
    # MÉTHODES OPTIONNELLES (surchargeables)
    # =========================================================
    
    def signaler_blocage(self):
        """Appelé par Engine quand trop d'échecs consécutifs
        
        Implémentation par défaut : log un warning.
        À surcharger pour gérer le reboot.
        """
        self.logger.warning(f"{self.nom}: Blocage signalé par le moteur")
    
    def initialiser_sequence(self):
        """Initialise la séquence d'actions
        
        Appelée une fois au démarrage.
        Implémentation par défaut vide.
        """
        pass
    
    def construire_sequence_selon_timers(self):
        """Construit la séquence d'actions selon les timers dus
        
        Implémentation par défaut vide.
        À surcharger si nécessaire.
        """
        pass
    
    # =========================================================
    # STATISTIQUES
    # =========================================================
    
    def incrementer_stat(self, nom_stat, valeur=1):
        """Incrémente une statistique
        
        Args:
            nom_stat: Nom de la stat ('actions_executees', 'erreurs_detectees', etc.)
            valeur: Valeur à ajouter (défaut: 1)
        """
        if nom_stat in self._stats:
            self._stats[nom_stat] += valeur
    
    def get_stats(self):
        """Retourne les statistiques locales
        
        Returns:
            dict: Copie des statistiques
        """
        return self._stats.copy()
    
    # =========================================================
    # MÉCANISME D'ATTENTE NON BLOQUANTE
    # =========================================================
    
    def demander_rotation(self):
        """Appelé par une Action pour demander à passer à la fenêtre suivante
        
        L'action reste dans la séquence et sera réexécutée au prochain tour.
        Utilisé par les actions d'attente non bloquante.
        """
        self._demande_rotation = True
        self.logger.debug("Rotation demandée par une action")
    
    def doit_tourner(self):
        """Vérifié par Engine après chaque action
        
        Returns:
            bool: True si rotation demandée (et reset le flag)
        """
        result = self._demande_rotation
        self._demande_rotation = False  # Reset automatique
        return result
    
    # =========================================================
    # SCHEDULING - PROCHAIN PASSAGE
    # =========================================================
    
    def get_prochain_passage_prioritaire(self):
        """Retourne dans combien de secondes traiter les actions prioritaires
        
        Regarde le premier slot de slots_prioritaires (trié par timestamp)
        et retourne le temps restant avant qu'il soit disponible.
        
        À surcharger dans les sous-classes si logique plus complexe.
        
        Returns:
            float: Secondes avant prochain traitement
                - <= 0 : prête maintenant
                - > 0  : revenir dans X secondes
                - float('inf') ou None : pas d'action prioritaire
        """
        if not self.slots_prioritaires:
            return float('inf')
        
        # Le premier slot est le plus urgent (liste triée)
        premier_slot = self.slots_prioritaires[0]
        prochain = premier_slot.get('prochain_disponible', 0)
        
        import time
        return prochain - time.time()
    
    def get_prochain_passage_normal(self):
        """Retourne dans combien de secondes traiter les actions normales
        
        Regarde le premier slot de slots_normaux (trié par timestamp)
        et retourne le temps restant avant qu'il soit disponible.
        
        À surcharger dans les sous-classes si logique plus complexe.
        
        Returns:
            float: Secondes avant prochain traitement
                - <= 0 : prête maintenant
                - > 0  : revenir dans X secondes
                - float('inf') ou None : pas d'action normale
        """
        if not self.slots_normaux:
            return float('inf')
        
        # Le premier slot est le plus urgent (liste triée)
        premier_slot = self.slots_normaux[0]
        prochain = premier_slot.get('prochain_disponible', 0)
        
        import time
        return prochain - time.time()
    
    
    def reset(self):
        """Réinitialise l'état du manoir"""
        self.termine = False
        self.variables.clear()
        self.boucles_actives.clear()
        self._etats_boucles.clear()
        self.sequence.clear()
        self.slots_prioritaires.clear()
        self.slots_normaux.clear()
        self.invalidate_capture()
        self.logger.info("Manoir réinitialisé")

    def __repr__(self):
        total_slots = sum(s['nb'] for s in self.slots_config)
        return f"{self.__class__.__name__}('{self.manoir_id}', slots={total_slots})"
