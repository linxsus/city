"""Gestionnaire ADB pour les appareils Android

Ce module gère les interactions avec les appareils Android via ADB :
- Détection des appareils connectés
- Capture d'écran
- Envoi de clics/touches
- Lancement de scrcpy
"""

import subprocess
import time
from io import BytesIO
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image

from utils.logger import get_module_logger

logger = get_module_logger("ADBManager")


class ADBManager:
    """Gestionnaire pour les commandes ADB

    Attributes:
        adb_path: Chemin vers l'exécutable adb
        scrcpy_path: Chemin vers l'exécutable scrcpy
        device_serial: Serial de l'appareil (None pour auto-détection)
        timeout: Timeout par défaut pour les commandes (secondes)
    """

    def __init__(
        self,
        adb_path: str = "adb",
        scrcpy_path: str = "scrcpy",
        device_serial: Optional[str] = None,
        timeout: int = 10
    ):
        """
        Args:
            adb_path: Chemin vers adb (défaut: utilise le PATH)
            scrcpy_path: Chemin vers scrcpy (défaut: utilise le PATH)
            device_serial: Serial de l'appareil (None pour auto-détection)
            timeout: Timeout des commandes en secondes
        """
        self.adb_path = adb_path
        self.scrcpy_path = scrcpy_path
        self.device_serial = device_serial
        self.timeout = timeout

        # Cache pour les infos de l'appareil
        self._device_name: Optional[str] = None
        self._screen_size: Optional[Tuple[int, int]] = None

    # =========================================================
    # DÉTECTION DES APPAREILS
    # =========================================================

    def get_connected_devices(self) -> list[dict]:
        """Liste les appareils Android connectés

        Returns:
            Liste de dictionnaires avec 'serial' et 'status'
            Ex: [{'serial': 'RF8M33XXXXX', 'status': 'device'}]
        """
        try:
            result = subprocess.run(
                [self.adb_path, "devices"],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            devices = []
            lines = result.stdout.strip().split('\n')[1:]  # Skip header

            for line in lines:
                if line.strip():
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        devices.append({
                            'serial': parts[0],
                            'status': parts[1]
                        })

            return devices

        except subprocess.TimeoutExpired:
            logger.error("Timeout lors de la détection des appareils")
            return []
        except FileNotFoundError:
            logger.error(f"ADB non trouvé: {self.adb_path}")
            return []
        except Exception as e:
            logger.error(f"Erreur détection appareils: {e}")
            return []

    def detect_device(self) -> Optional[str]:
        """Détecte automatiquement l'appareil connecté

        Si device_serial est défini, vérifie qu'il est connecté.
        Sinon, retourne le premier appareil trouvé.

        Returns:
            Serial de l'appareil ou None
        """
        devices = self.get_connected_devices()

        if not devices:
            logger.warning("Aucun appareil Android connecté")
            return None

        # Filtrer les appareils prêts (status = 'device')
        ready_devices = [d for d in devices if d['status'] == 'device']

        if not ready_devices:
            statuses = [f"{d['serial']}:{d['status']}" for d in devices]
            logger.warning(f"Appareils non prêts: {statuses}")
            return None

        # Si serial spécifié, vérifier qu'il est dans la liste
        if self.device_serial:
            for device in ready_devices:
                if device['serial'] == self.device_serial:
                    return self.device_serial
            logger.warning(f"Appareil {self.device_serial} non trouvé")
            return None

        # Auto-détection : prendre le premier
        serial = ready_devices[0]['serial']
        self.device_serial = serial
        logger.info(f"Appareil détecté: {serial}")
        return serial

    def is_device_connected(self) -> bool:
        """Vérifie si un appareil est connecté et prêt

        Returns:
            bool: True si appareil prêt
        """
        return self.detect_device() is not None

    def get_device_name(self) -> Optional[str]:
        """Récupère le nom/modèle de l'appareil

        Returns:
            Nom de l'appareil (ex: "SM-G950F") ou None
        """
        if self._device_name:
            return self._device_name

        if not self.device_serial:
            self.detect_device()

        if not self.device_serial:
            return None

        try:
            result = subprocess.run(
                [self.adb_path, "-s", self.device_serial, "shell",
                 "getprop", "ro.product.model"],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            name = result.stdout.strip()
            if name:
                self._device_name = name
                return name

        except Exception as e:
            logger.error(f"Erreur récupération nom appareil: {e}")

        return None

    # =========================================================
    # CAPTURE D'ÉCRAN
    # =========================================================

    def capture_screen(self) -> Optional[Image.Image]:
        """Capture l'écran de l'appareil via ADB

        Returns:
            PIL.Image en RGB ou None si erreur
        """
        if not self.device_serial:
            self.detect_device()

        if not self.device_serial:
            logger.error("Pas d'appareil pour la capture")
            return None

        try:
            # Capture PNG directe via exec-out (plus rapide)
            result = subprocess.run(
                [self.adb_path, "-s", self.device_serial,
                 "exec-out", "screencap", "-p"],
                capture_output=True,
                timeout=self.timeout
            )

            if result.returncode != 0:
                logger.error(f"Erreur capture: {result.stderr.decode()}")
                return None

            # Charger l'image depuis les bytes
            image = Image.open(BytesIO(result.stdout))

            # Convertir en RGB si nécessaire
            if image.mode != 'RGB':
                image = image.convert('RGB')

            return image

        except subprocess.TimeoutExpired:
            logger.error("Timeout capture d'écran")
            return None
        except Exception as e:
            logger.error(f"Erreur capture écran: {e}")
            return None

    def save_screenshot(self, filepath: str) -> bool:
        """Capture et sauvegarde une capture d'écran

        Args:
            filepath: Chemin de sauvegarde

        Returns:
            bool: True si succès
        """
        image = self.capture_screen()
        if image:
            try:
                image.save(filepath)
                logger.debug(f"Capture sauvegardée: {filepath}")
                return True
            except Exception as e:
                logger.error(f"Erreur sauvegarde capture: {e}")
        return False

    def get_screen_size(self) -> Optional[Tuple[int, int]]:
        """Récupère la taille de l'écran de l'appareil

        Returns:
            Tuple (largeur, hauteur) ou None
        """
        if self._screen_size:
            return self._screen_size

        if not self.device_serial:
            self.detect_device()

        if not self.device_serial:
            return None

        try:
            result = subprocess.run(
                [self.adb_path, "-s", self.device_serial, "shell",
                 "wm", "size"],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            # Output: "Physical size: 1080x1920"
            output = result.stdout.strip()
            if "x" in output:
                # Prendre la dernière ligne contenant les dimensions
                for line in output.split('\n'):
                    if 'x' in line:
                        size_part = line.split(':')[-1].strip()
                        width, height = map(int, size_part.split('x'))
                        self._screen_size = (width, height)
                        return self._screen_size

        except Exception as e:
            logger.error(f"Erreur récupération taille écran: {e}")

        return None

    # =========================================================
    # INTERACTIONS (CLICS, TOUCHES)
    # =========================================================

    def tap(self, x: int, y: int) -> bool:
        """Effectue un tap (clic) à une position

        Args:
            x, y: Coordonnées du tap

        Returns:
            bool: True si succès
        """
        if not self.device_serial:
            self.detect_device()

        if not self.device_serial:
            logger.error("Pas d'appareil pour le tap")
            return False

        try:
            result = subprocess.run(
                [self.adb_path, "-s", self.device_serial, "shell",
                 "input", "tap", str(int(x)), str(int(y))],
                capture_output=True,
                timeout=self.timeout
            )

            if result.returncode == 0:
                logger.debug(f"Tap à ({x}, {y})")
                return True
            else:
                logger.error(f"Erreur tap: {result.stderr.decode()}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("Timeout tap")
            return False
        except Exception as e:
            logger.error(f"Erreur tap: {e}")
            return False

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300) -> bool:
        """Effectue un swipe (glissement)

        Args:
            x1, y1: Position de départ
            x2, y2: Position d'arrivée
            duration_ms: Durée du swipe en millisecondes

        Returns:
            bool: True si succès
        """
        if not self.device_serial:
            self.detect_device()

        if not self.device_serial:
            logger.error("Pas d'appareil pour le swipe")
            return False

        try:
            result = subprocess.run(
                [self.adb_path, "-s", self.device_serial, "shell",
                 "input", "swipe",
                 str(int(x1)), str(int(y1)),
                 str(int(x2)), str(int(y2)),
                 str(duration_ms)],
                capture_output=True,
                timeout=self.timeout
            )

            if result.returncode == 0:
                logger.debug(f"Swipe ({x1},{y1}) -> ({x2},{y2})")
                return True
            else:
                logger.error(f"Erreur swipe: {result.stderr.decode()}")
                return False

        except Exception as e:
            logger.error(f"Erreur swipe: {e}")
            return False

    def long_press(self, x: int, y: int, duration_ms: int = 1000) -> bool:
        """Effectue un appui long

        Args:
            x, y: Coordonnées
            duration_ms: Durée de l'appui en millisecondes

        Returns:
            bool: True si succès
        """
        # Un long press est un swipe sans mouvement
        return self.swipe(x, y, x, y, duration_ms)

    def input_text(self, text: str) -> bool:
        """Saisit du texte

        Args:
            text: Texte à saisir (ASCII uniquement)

        Returns:
            bool: True si succès
        """
        if not self.device_serial:
            self.detect_device()

        if not self.device_serial:
            logger.error("Pas d'appareil pour la saisie")
            return False

        # Échapper les caractères spéciaux shell
        # Remplacer les espaces par %s (format ADB)
        escaped_text = text.replace(' ', '%s')

        try:
            result = subprocess.run(
                [self.adb_path, "-s", self.device_serial, "shell",
                 "input", "text", escaped_text],
                capture_output=True,
                timeout=self.timeout
            )

            if result.returncode == 0:
                logger.debug(f"Texte saisi: {text[:20]}...")
                return True
            else:
                logger.error(f"Erreur saisie texte: {result.stderr.decode()}")
                return False

        except Exception as e:
            logger.error(f"Erreur saisie texte: {e}")
            return False

    def press_key(self, keycode: int) -> bool:
        """Appuie sur une touche (keycode Android)

        Keycodes courants:
        - 3: HOME
        - 4: BACK
        - 24: VOLUME_UP
        - 25: VOLUME_DOWN
        - 26: POWER
        - 66: ENTER
        - 82: MENU

        Args:
            keycode: Code de la touche Android

        Returns:
            bool: True si succès
        """
        if not self.device_serial:
            self.detect_device()

        if not self.device_serial:
            logger.error("Pas d'appareil pour la touche")
            return False

        try:
            result = subprocess.run(
                [self.adb_path, "-s", self.device_serial, "shell",
                 "input", "keyevent", str(keycode)],
                capture_output=True,
                timeout=self.timeout
            )

            if result.returncode == 0:
                logger.debug(f"Touche pressée: {keycode}")
                return True
            else:
                logger.error(f"Erreur touche: {result.stderr.decode()}")
                return False

        except Exception as e:
            logger.error(f"Erreur touche: {e}")
            return False

    def press_back(self) -> bool:
        """Appuie sur le bouton Retour"""
        return self.press_key(4)

    def press_home(self) -> bool:
        """Appuie sur le bouton Home"""
        return self.press_key(3)

    def press_enter(self) -> bool:
        """Appuie sur Entrée"""
        return self.press_key(66)

    # =========================================================
    # SCRCPY
    # =========================================================

    def launch_scrcpy(
        self,
        max_size: int = 1024,
        bit_rate: str = "8M",
        window_title: Optional[str] = None,
        stay_awake: bool = True,
        turn_screen_off: bool = False,
        extra_args: Optional[list] = None
    ) -> Optional[subprocess.Popen]:
        """Lance scrcpy pour afficher l'écran de l'appareil

        Args:
            max_size: Taille max de la dimension la plus grande (option -m)
            bit_rate: Bitrate vidéo (ex: "8M", "4M")
            window_title: Titre de la fenêtre (défaut: nom de l'appareil)
            stay_awake: Garder l'appareil éveillé
            turn_screen_off: Éteindre l'écran de l'appareil
            extra_args: Arguments supplémentaires

        Returns:
            Popen si lancé, None si erreur
        """
        if not self.device_serial:
            self.detect_device()

        if not self.device_serial:
            logger.error("Pas d'appareil pour scrcpy")
            return None

        cmd = [
            self.scrcpy_path,
            "-s", self.device_serial,
            "-m", str(max_size),
            "-b", bit_rate,
        ]

        if window_title:
            cmd.extend(["--window-title", window_title])

        if stay_awake:
            cmd.append("--stay-awake")

        if turn_screen_off:
            cmd.append("--turn-screen-off")

        if extra_args:
            cmd.extend(extra_args)

        try:
            # Lancer en arrière-plan (non-bloquant)
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            logger.info(f"Scrcpy lancé (PID: {process.pid})")
            return process

        except FileNotFoundError:
            logger.error(f"Scrcpy non trouvé: {self.scrcpy_path}")
            return None
        except Exception as e:
            logger.error(f"Erreur lancement scrcpy: {e}")
            return None

    def is_scrcpy_running(self) -> bool:
        """Vérifie si scrcpy est en cours d'exécution

        Returns:
            bool: True si scrcpy est lancé
        """
        try:
            # Sous Windows, chercher scrcpy.exe dans les processus
            import platform
            if platform.system() == "Windows":
                result = subprocess.run(
                    ["tasklist", "/FI", "IMAGENAME eq scrcpy.exe"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                return "scrcpy.exe" in result.stdout
            else:
                # Sous Linux/Mac, utiliser pgrep
                result = subprocess.run(
                    ["pgrep", "-x", "scrcpy"],
                    capture_output=True,
                    timeout=5
                )
                return result.returncode == 0

        except Exception:
            return False

    # =========================================================
    # UTILITAIRES
    # =========================================================

    def run_shell_command(self, command: str) -> Optional[str]:
        """Exécute une commande shell sur l'appareil

        Args:
            command: Commande à exécuter

        Returns:
            Sortie de la commande ou None
        """
        if not self.device_serial:
            self.detect_device()

        if not self.device_serial:
            return None

        try:
            result = subprocess.run(
                [self.adb_path, "-s", self.device_serial, "shell", command],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            return result.stdout.strip()

        except Exception as e:
            logger.error(f"Erreur commande shell: {e}")
            return None

    def wake_screen(self) -> bool:
        """Réveille l'écran de l'appareil

        Returns:
            bool: True si succès
        """
        return self.press_key(224)  # KEYCODE_WAKEUP

    def is_screen_on(self) -> bool:
        """Vérifie si l'écran de l'appareil est allumé

        Returns:
            bool: True si écran allumé
        """
        output = self.run_shell_command("dumpsys power | grep 'Display Power'")
        if output:
            return "state=ON" in output
        return False

    def clear_cache(self):
        """Réinitialise le cache interne"""
        self._device_name = None
        self._screen_size = None
        self.device_serial = None


# Singleton
_adb_manager: Optional[ADBManager] = None


def get_adb_manager() -> ADBManager:
    """Retourne l'instance singleton du gestionnaire ADB

    Returns:
        ADBManager: Instance partagée
    """
    global _adb_manager
    if _adb_manager is None:
        _adb_manager = ADBManager()
    return _adb_manager
