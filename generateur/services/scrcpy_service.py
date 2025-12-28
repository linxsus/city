"""Service de capture d'écran via scrcpy/ADB pour le générateur.

Ce service permet de capturer directement l'écran depuis un appareil Android
connecté via ADB, sans avoir besoin d'uploader manuellement des captures.
"""

import base64
import time
import uuid
from io import BytesIO
from pathlib import Path
from typing import Optional

from PIL import Image

from ..config import UPLOAD_DIR, FRAMEWORK_TEMPLATES_DIR

# Taille max par défaut pour les captures (cohérent avec scrcpy_max_size)
DEFAULT_MAX_SIZE = 1024


class ScrcpyService:
    """Service pour les captures d'écran via ADB/scrcpy.

    Permet de :
    - Détecter les appareils Android connectés
    - Capturer l'écran directement
    - Sauvegarder les captures pour utilisation dans le générateur
    """

    def __init__(self, adb_path: str = "adb", scrcpy_path: str = "scrcpy", max_size: int = DEFAULT_MAX_SIZE):
        """
        Args:
            adb_path: Chemin vers l'exécutable adb
            scrcpy_path: Chemin vers l'exécutable scrcpy
            max_size: Taille max de la dimension la plus grande (défaut: 1024)
        """
        self.adb_path = adb_path
        self.scrcpy_path = scrcpy_path
        self.max_size = max_size
        self._adb_manager = None
        self._manoir = None
        # Dimensions de l'écran réel (mises à jour après capture)
        self._real_screen_size: Optional[tuple] = None
        # Dimensions après redimensionnement
        self._resized_size: Optional[tuple] = None

    def _get_adb_manager(self):
        """Récupère ou crée le gestionnaire ADB."""
        if self._adb_manager is None:
            # Importer ici pour éviter les imports circulaires
            from core.adb_manager import ADBManager
            from manoirs.config_manoirs import get_config

            # Charger la config si disponible
            config = get_config("android") or {}

            # Utiliser max_size de la config si disponible
            if "scrcpy_max_size" in config:
                self.max_size = config["scrcpy_max_size"]

            self._adb_manager = ADBManager(
                adb_path=config.get("adb_path", self.adb_path),
                scrcpy_path=config.get("scrcpy_path", self.scrcpy_path),
                device_serial=config.get("device_serial"),
            )
        return self._adb_manager

    def _get_manoir(self):
        """Récupère ou crée le manoir scrcpy."""
        if self._manoir is None:
            try:
                from manoirs.instances.manoir_scrcpy_exemple import creer_manoir_scrcpy
                self._manoir = creer_manoir_scrcpy()
            except Exception:
                # Fallback sur ADB direct
                self._manoir = None
        return self._manoir

    def _resize_image(self, image: Image.Image) -> Image.Image:
        """Redimensionne l'image pour que la plus grande dimension soit <= max_size.

        Args:
            image: Image PIL à redimensionner

        Returns:
            Image redimensionnée (ou originale si déjà assez petite)
        """
        if self.max_size <= 0:
            return image

        width, height = image.size
        max_dim = max(width, height)

        if max_dim <= self.max_size:
            return image

        # Calculer le ratio de redimensionnement
        ratio = self.max_size / max_dim
        new_width = int(width * ratio)
        new_height = int(height * ratio)

        # Redimensionner avec un bon algorithme
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    def get_status(self) -> dict:
        """Récupère le statut de la connexion ADB.

        Returns:
            Dict avec les infos de connexion
        """
        adb = self._get_adb_manager()

        devices = adb.get_connected_devices()
        connected = adb.is_device_connected()

        result = {
            "connected": connected,
            "devices": devices,
            "device_serial": adb.device_serial,
            "device_name": None,
            "screen_size": None,
            "max_size": self.max_size,
        }

        if connected:
            result["device_name"] = adb.get_device_name()
            result["screen_size"] = adb.get_screen_size()

        return result

    def capture_screen(self) -> Optional[Image.Image]:
        """Capture l'écran de l'appareil Android.

        L'image est automatiquement redimensionnée pour que la plus grande
        dimension soit <= max_size (défaut: 1024).

        Returns:
            PIL.Image ou None si erreur
        """
        image = None

        # Essayer d'abord via le manoir
        manoir = self._get_manoir()
        if manoir:
            try:
                image = manoir.capture(force=True)
            except Exception:
                pass

        # Fallback sur ADB direct
        if image is None:
            adb = self._get_adb_manager()
            image = adb.capture_screen()

        # Stocker les dimensions originales et redimensionner
        if image is not None:
            self._real_screen_size = image.size
            image = self._resize_image(image)
            self._resized_size = image.size

        return image

    def capture_and_save(self, prefix: str = "capture") -> Optional[dict]:
        """Capture l'écran et sauvegarde le fichier.

        Args:
            prefix: Préfixe du nom de fichier

        Returns:
            Dict avec les infos de la capture ou None
        """
        image = self.capture_screen()
        if not image:
            return None

        # Générer un nom unique
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        filename = f"{prefix}_{timestamp}_{unique_id}.png"

        # Sauvegarder dans le dossier uploads
        filepath = UPLOAD_DIR / filename
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        try:
            image.save(str(filepath), "PNG")

            return {
                "path": str(filepath),
                "filename": filename,
                "width": image.width,
                "height": image.height,
                "size_bytes": filepath.stat().st_size,
            }
        except Exception as e:
            return None

    def capture_to_base64(self) -> Optional[dict]:
        """Capture l'écran et retourne en base64 (pour affichage direct).

        Returns:
            Dict avec data URL et infos ou None
        """
        image = self.capture_screen()
        if not image:
            return None

        # Convertir en base64
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)

        b64_data = base64.b64encode(buffer.read()).decode("utf-8")
        data_url = f"data:image/png;base64,{b64_data}"

        return {
            "data_url": data_url,
            "width": image.width,
            "height": image.height,
        }

    def save_for_template(
        self,
        template_name: str,
        subdir: str = "scrcpy",
        region: Optional[tuple] = None,
    ) -> Optional[dict]:
        """Capture et sauvegarde directement comme template.

        Args:
            template_name: Nom du template (sans extension)
            subdir: Sous-dossier dans templates/
            region: Région à extraire (x, y, width, height) optionnelle

        Returns:
            Dict avec les infos du template ou None
        """
        image = self.capture_screen()
        if not image:
            return None

        # Extraire la région si spécifiée
        if region:
            x, y, w, h = region
            image = image.crop((x, y, x + w, y + h))

        # Créer le dossier de destination
        dest_dir = FRAMEWORK_TEMPLATES_DIR / subdir
        dest_dir.mkdir(parents=True, exist_ok=True)

        # Sauvegarder
        filename = f"{template_name}.png"
        filepath = dest_dir / filename

        try:
            image.save(str(filepath), "PNG")

            # Chemin relatif pour utilisation dans le code
            relative_path = f"{subdir}/{filename}"

            return {
                "path": str(filepath),
                "relative_path": relative_path,
                "filename": filename,
                "width": image.width,
                "height": image.height,
            }
        except Exception as e:
            return None

    def _convert_click_coordinates(self, x: int, y: int) -> tuple:
        """Convertit les coordonnées de l'image redimensionnée vers l'écran réel.

        Args:
            x, y: Coordonnées sur l'image redimensionnée

        Returns:
            Tuple (x, y) en coordonnées écran réel
        """
        if self._real_screen_size and self._resized_size:
            real_w, real_h = self._real_screen_size
            resized_w, resized_h = self._resized_size

            # Calculer le ratio
            scale_x = real_w / resized_w
            scale_y = real_h / resized_h

            return (int(x * scale_x), int(y * scale_y))

        return (x, y)

    def click_at(self, x: int, y: int) -> bool:
        """Effectue un clic sur l'appareil.

        Les coordonnées sont relatives à l'image redimensionnée (max 1024px)
        et sont automatiquement converties vers les coordonnées réelles de l'écran.

        Args:
            x, y: Coordonnées du clic (sur l'image redimensionnée)

        Returns:
            True si succès
        """
        # Convertir les coordonnées vers l'écran réel
        real_x, real_y = self._convert_click_coordinates(x, y)

        # Essayer via le manoir
        manoir = self._get_manoir()
        if manoir:
            try:
                manoir.click_at(real_x, real_y)
                return True
            except Exception:
                pass

        # Fallback sur ADB direct
        adb = self._get_adb_manager()
        return adb.tap(real_x, real_y)

    def press_back(self) -> bool:
        """Appuie sur le bouton retour."""
        adb = self._get_adb_manager()
        return adb.press_back()

    def press_home(self) -> bool:
        """Appuie sur le bouton home."""
        adb = self._get_adb_manager()
        return adb.press_home()

    def launch_scrcpy_window(self) -> bool:
        """Lance scrcpy pour visualiser l'écran.

        Returns:
            True si lancé avec succès
        """
        adb = self._get_adb_manager()
        process = adb.launch_scrcpy(window_title="Générateur - Preview")
        return process is not None

    def is_scrcpy_running(self) -> bool:
        """Vérifie si scrcpy est en cours."""
        adb = self._get_adb_manager()
        return adb.is_scrcpy_running()


# Singleton
_scrcpy_service: Optional[ScrcpyService] = None


def get_scrcpy_service() -> ScrcpyService:
    """Retourne l'instance singleton du service scrcpy."""
    global _scrcpy_service
    if _scrcpy_service is None:
        _scrcpy_service = ScrcpyService()
    return _scrcpy_service
