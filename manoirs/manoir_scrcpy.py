"""Manoir pour appareils Android via scrcpy/ADB

Ce manoir permet d'automatiser un appareil Android connecté en USB.
Toutes les interactions (capture d'écran, clics) passent par ADB,
ce qui permet de fonctionner même sans fenêtre scrcpy visible.

Caractéristiques :
- Capture d'écran via ADB (adb exec-out screencap)
- Clics via ADB (adb shell input tap)
- Auto-détection de l'appareil USB
- Lancement optionnel de scrcpy pour visualisation
- Sauvegarde des captures pour le générateur de templates
"""

import subprocess
import time
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from PIL import Image

from core.adb_manager import ADBManager, get_adb_manager
from manoirs.manoir_base import ManoirBase
from utils.config import CAPTURES_DIR, TEMPLATES_DIR

if TYPE_CHECKING:
    pass


class ManoirScrcpy(ManoirBase):
    """Manoir pour appareil Android via ADB

    Surcharge les méthodes de capture et d'interaction de ManoirBase
    pour utiliser ADB au lieu de la capture de fenêtre Windows.

    Attributes:
        adb: Instance du gestionnaire ADB
        scrcpy_max_size: Taille max pour scrcpy (option -m)
        scrcpy_process: Processus scrcpy si lancé
        templates_subdir: Sous-dossier pour les templates spécifiques
    """

    def __init__(
        self,
        manoir_id: str,
        nom: Optional[str] = None,
        adb_path: str = "adb",
        scrcpy_path: str = "scrcpy",
        device_serial: Optional[str] = None,
        scrcpy_max_size: int = 1024,
        largeur: int = 1024,
        hauteur: int = 576,
        priorite: int = 50,
        slots_config: Optional[list] = None,
        templates_subdir: str = "scrcpy",
    ):
        """
        Args:
            manoir_id: Identifiant unique
            nom: Nom affichable (défaut = manoir_id)
            adb_path: Chemin vers adb
            scrcpy_path: Chemin vers scrcpy
            device_serial: Serial de l'appareil (None pour auto-détection)
            scrcpy_max_size: Taille max pour scrcpy (option -m)
            largeur: Largeur de référence pour les coordonnées
            hauteur: Hauteur de référence pour les coordonnées
            priorite: Priorité (0-100)
            slots_config: Configuration des slots
            templates_subdir: Sous-dossier pour les templates
        """
        # Créer le gestionnaire ADB dédié à ce manoir
        self.adb = ADBManager(
            adb_path=adb_path,
            scrcpy_path=scrcpy_path,
            device_serial=device_serial
        )

        self.scrcpy_max_size = scrcpy_max_size
        self.scrcpy_process: Optional[subprocess.Popen] = None
        self.templates_subdir = templates_subdir

        # Dimensions réelles de l'écran Android (détectées)
        self._screen_width: Optional[int] = None
        self._screen_height: Optional[int] = None

        # Appeler le constructeur parent
        # Note: titre_bluestacks n'est pas utilisé pour scrcpy
        # mais on le définit pour compatibilité
        super().__init__(
            manoir_id=manoir_id,
            nom=nom,
            titre_bluestacks=f"scrcpy_{manoir_id}",
            largeur=largeur,
            hauteur=hauteur,
            priorite=priorite,
            slots_config=slots_config,
            position_x=None,  # Pas de gestion de position Windows
            position_y=None,
        )

        # Créer le dossier de templates spécifique
        self._templates_dir = TEMPLATES_DIR / templates_subdir
        self._templates_dir.mkdir(parents=True, exist_ok=True)

    # =========================================================
    # SURCHARGES - GESTION APPAREIL (remplace fenêtre Windows)
    # =========================================================

    def find_window(self):
        """Détecte l'appareil Android au lieu de la fenêtre Windows

        Returns:
            str ou None: Serial de l'appareil
        """
        serial = self.adb.detect_device()
        if serial:
            self._hwnd = serial  # Réutilise _hwnd pour stocker le serial
            self._detect_screen_dimensions()
        return serial

    def _detect_screen_dimensions(self):
        """Détecte les dimensions réelles de l'écran Android"""
        size = self.adb.get_screen_size()
        if size:
            self._screen_width, self._screen_height = size
            self.logger.info(f"Écran Android: {self._screen_width}x{self._screen_height}")

    def activate(self):
        """Réveille l'appareil si nécessaire

        Returns:
            bool: True si appareil prêt
        """
        if not self._hwnd:
            self.find_window()

        if not self._hwnd:
            self.logger.warning("Aucun appareil Android connecté")
            return False

        # Réveiller l'écran si éteint
        if not self.adb.is_screen_on():
            self.adb.wake_screen()
            time.sleep(0.5)

        return True

    def placer_fenetre(self):
        """Non utilisé pour scrcpy (pas de fenêtre à placer)

        Returns:
            bool: True toujours
        """
        return True

    def is_valid(self):
        """Vérifie si l'appareil est connecté

        Returns:
            bool: True si appareil connecté et prêt
        """
        return self.adb.is_device_connected()

    def get_rect(self):
        """Retourne les dimensions de l'écran

        Returns:
            Tuple (0, 0, largeur, hauteur)
        """
        if self._screen_width and self._screen_height:
            return (0, 0, self._screen_width, self._screen_height)

        # Fallback sur les dimensions de référence
        return (0, 0, self.largeur, self.hauteur)

    # =========================================================
    # SURCHARGES - CAPTURE D'ÉCRAN VIA ADB
    # =========================================================

    def capture(self, force=False):
        """Capture l'écran via ADB

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

        # Capture via ADB
        image = self.adb.capture_screen()

        if image:
            self._derniere_capture = image
            self._capture_timestamp = now

            # Mettre à jour les dimensions si nécessaire
            if not self._screen_width:
                self._screen_width, self._screen_height = image.size
                self.logger.debug(f"Dimensions détectées: {image.size}")

        return image

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
            image.save(str(filepath))
            self.logger.info(f"Capture sauvegardée: {filepath}")
            return filepath
        except Exception as e:
            self.logger.error(f"Erreur sauvegarde capture: {e}")
            return None

    def save_capture_for_template(self, template_name: str, region: Optional[tuple] = None):
        """Sauvegarde une capture pour utilisation comme template

        Sauvegarde dans le dossier templates/scrcpy/ pour être utilisé
        avec le générateur.

        Args:
            template_name: Nom du fichier template (sans extension)
            region: Région à extraire (x, y, w, h) optionnelle

        Returns:
            Path ou None: Chemin du fichier sauvegardé
        """
        image = self.capture(force=True)
        if not image:
            return None

        # Extraire la région si spécifiée
        if region:
            x, y, w, h = region
            image = image.crop((x, y, x + w, y + h))

        # Sauvegarder dans le dossier templates
        filename = f"{template_name}.png"
        filepath = self._templates_dir / filename

        try:
            image.save(str(filepath))
            self.logger.info(f"Template sauvegardé: {filepath}")
            return filepath
        except Exception as e:
            self.logger.error(f"Erreur sauvegarde template: {e}")
            return None

    # =========================================================
    # SURCHARGES - INTERACTIONS VIA ADB
    # =========================================================

    def click_at(self, x, y, relative=False):
        """Effectue un clic via ADB

        Args:
            x, y: Position du clic
            relative: Si True, coordonnées relatives (0-1)
        """
        if relative:
            # Convertir les coordonnées relatives en absolues
            x = int(x * self.largeur)
            y = int(y * self.hauteur)

        # Convertir les coordonnées de référence vers les coordonnées réelles
        screen_x, screen_y = self._convert_coordinates(x, y)

        self.adb.tap(screen_x, screen_y)
        self.logger.debug(f"Tap ADB à ({screen_x}, {screen_y})")

        # Invalider le cache de capture
        self.invalidate_capture()

    def _convert_coordinates(self, x: int, y: int) -> tuple:
        """Convertit les coordonnées de référence vers les coordonnées écran réelles

        Les coordonnées sont données en référence (largeur x hauteur),
        il faut les convertir vers les dimensions réelles de l'écran Android.

        Args:
            x, y: Coordonnées en référence

        Returns:
            Tuple (x, y) en coordonnées écran
        """
        if not self._screen_width or not self._screen_height:
            # Pas de conversion si dimensions inconnues
            return (x, y)

        # Calculer le ratio
        scale_x = self._screen_width / self.largeur
        scale_y = self._screen_height / self.hauteur

        return (int(x * scale_x), int(y * scale_y))

    def _perform_click(self, screen_x, screen_y):
        """Effectue le clic via ADB (PROTÉGÉ)

        Surcharge de ManoirBase pour utiliser ADB au lieu de pyautogui.
        """
        self.adb.tap(screen_x, screen_y)

    def type_text(self, text, interval=0.05):
        """Saisit du texte via ADB

        Args:
            text: Texte à saisir
            interval: Non utilisé (ADB envoie tout d'un coup)
        """
        self.adb.input_text(text)
        self.invalidate_capture()

    def press_key(self, key):
        """Appuie sur une touche

        Args:
            key: Touche à presser ('enter', 'escape', 'back', 'home')
                 ou un keycode Android (int)
        """
        # Mapping des noms de touches vers les keycodes Android
        key_map = {
            'enter': 66,
            'escape': 4,  # BACK
            'back': 4,
            'home': 3,
            'menu': 82,
            'power': 26,
            'volume_up': 24,
            'volume_down': 25,
        }

        if isinstance(key, str):
            keycode = key_map.get(key.lower())
            if keycode is None:
                self.logger.warning(f"Touche inconnue: {key}")
                return
        else:
            keycode = key

        self.adb.press_key(keycode)
        self.invalidate_capture()

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300):
        """Effectue un swipe (glissement)

        Args:
            x1, y1: Position de départ
            x2, y2: Position d'arrivée
            duration_ms: Durée en millisecondes
        """
        # Convertir les coordonnées
        sx1, sy1 = self._convert_coordinates(x1, y1)
        sx2, sy2 = self._convert_coordinates(x2, y2)

        self.adb.swipe(sx1, sy1, sx2, sy2, duration_ms)
        self.invalidate_capture()

    def long_press(self, x: int, y: int, duration_ms: int = 1000):
        """Effectue un appui long

        Args:
            x, y: Coordonnées
            duration_ms: Durée en millisecondes
        """
        screen_x, screen_y = self._convert_coordinates(x, y)
        self.adb.long_press(screen_x, screen_y, duration_ms)
        self.invalidate_capture()

    # =========================================================
    # GESTION SCRCPY
    # =========================================================

    def launch_scrcpy(self, window_title: Optional[str] = None):
        """Lance scrcpy pour visualiser l'écran

        Args:
            window_title: Titre de la fenêtre (défaut: nom du manoir)

        Returns:
            bool: True si lancé avec succès
        """
        if self.is_scrcpy_running():
            self.logger.info("Scrcpy déjà en cours")
            return True

        title = window_title or f"Scrcpy - {self.nom}"

        self.scrcpy_process = self.adb.launch_scrcpy(
            max_size=self.scrcpy_max_size,
            window_title=title
        )

        if self.scrcpy_process:
            self.logger.info(f"Scrcpy lancé: {title}")
            return True

        return False

    def is_scrcpy_running(self) -> bool:
        """Vérifie si scrcpy est en cours d'exécution

        Returns:
            bool: True si scrcpy est lancé
        """
        # Vérifier le processus local si on l'a lancé
        if self.scrcpy_process:
            poll = self.scrcpy_process.poll()
            if poll is None:
                return True  # Toujours en cours
            else:
                self.scrcpy_process = None  # Terminé

        # Vérifier via le gestionnaire ADB (peut avoir été lancé ailleurs)
        return self.adb.is_scrcpy_running()

    def stop_scrcpy(self):
        """Arrête scrcpy"""
        if self.scrcpy_process:
            self.scrcpy_process.terminate()
            self.scrcpy_process = None
            self.logger.info("Scrcpy arrêté")

    # =========================================================
    # RÉSOLUTION DES TEMPLATES
    # =========================================================

    def _resolve_template_path(self, path):
        """Résout le chemin d'un template

        Cherche d'abord dans templates/scrcpy/, puis dans templates/.
        """
        path = Path(path)
        if path.is_absolute():
            return str(path)

        # Essayer dans templates/scrcpy/
        scrcpy_path = self._templates_dir / path
        if scrcpy_path.exists():
            return str(scrcpy_path)

        # Fallback sur templates/
        full_path = TEMPLATES_DIR / path
        if full_path.exists():
            return str(full_path)

        return str(path)

    # =========================================================
    # HOOKS ET CALLBACKS
    # =========================================================

    def _hook_reprise_changement(self):
        """Hook appelé lors de la reprise après changement de manoir

        Vérifie que l'appareil est toujours connecté et réveille l'écran.
        """
        # Vérifier la connexion
        if not self.adb.is_device_connected():
            self.logger.warning("Appareil déconnecté, tentative de reconnexion...")
            self.adb.clear_cache()
            self.find_window()

        # Réveiller l'écran
        self.activate()

    # =========================================================
    # MÉTHODES ABSTRAITES À IMPLÉMENTER PAR LES SOUS-CLASSES
    # =========================================================

    def _preparer_alimenter_sequence(self):
        """Alimente la séquence avec les actions à exécuter

        À implémenter dans les sous-classes concrètes.

        Returns:
            bool: True si prêt à exécuter
        """
        # Implémentation de base : vérifier l'état et naviguer
        if not self.verifier_etat():
            self.logger.warning("État inconnu, impossible d'alimenter la séquence")
            return False

        # Les sous-classes doivent implémenter leur logique ici
        return True

    def definir_timers(self):
        """Définit les timers pour ce manoir

        À implémenter dans les sous-classes concrètes.
        """
        pass

    # =========================================================
    # UTILITAIRES
    # =========================================================

    def get_device_info(self) -> dict:
        """Retourne les informations sur l'appareil connecté

        Returns:
            dict avec les infos de l'appareil
        """
        return {
            'serial': self.adb.device_serial,
            'name': self.adb.get_device_name(),
            'screen_size': self.adb.get_screen_size(),
            'scrcpy_running': self.is_scrcpy_running(),
            'screen_on': self.adb.is_screen_on(),
        }

    def __repr__(self):
        device = self.adb.device_serial or "non connecté"
        return f"ManoirScrcpy('{self.manoir_id}', device='{device}')"
