"""Détection et analyse de couleurs"""

import numpy as np
from PIL import Image

from utils.logger import get_module_logger

logger = get_module_logger("ColorDetector")


class ColorDetector:
    """Détection et vérification de couleurs dans des images"""

    def __init__(self):
        pass

    def _to_numpy_rgb(self, image):
        """Convertit une image en numpy array RGB (PROTÉGÉ)

        Args:
            image: PIL.Image ou numpy.ndarray

        Returns:
            numpy.ndarray: Image en RGB
        """
        if isinstance(image, Image.Image):
            return np.array(image)
        elif isinstance(image, np.ndarray):
            return image
        else:
            raise TypeError(f"Type d'image non supporté: {type(image)}")

    def get_color_at(self, image, x, y):
        """Obtient la couleur à une position

        Args:
            image: PIL.Image ou numpy.ndarray
            x, y: Coordonnées du pixel

        Returns:
            Tuple (r, g, b): Couleur RGB
        """
        try:
            if isinstance(image, Image.Image):
                pixel = image.getpixel((x, y))
                # Gérer les images avec alpha
                if len(pixel) == 4:
                    return pixel[:3]
                return pixel
            else:
                # numpy array (RGB)
                return tuple(image[y, x][:3])
        except Exception as e:
            logger.error(f"Erreur get_color_at({x}, {y}): {e}")
            return None

    def check_color_at(self, image, x, y, expected_rgb, tolerance=10):
        """Vérifie si la couleur à une position correspond

        Args:
            image: PIL.Image ou numpy.ndarray
            x, y: Coordonnées du pixel
            expected_rgb: Tuple (r, g, b) attendu
            tolerance: Tolérance par composante (0-255)

        Returns:
            bool: True si la couleur correspond
        """
        pixel = self.get_color_at(image, x, y)

        if pixel is None:
            return False

        # Vérifier chaque composante
        for i in range(3):
            if abs(pixel[i] - expected_rgb[i]) > tolerance:
                return False

        return True

    def find_color(self, image, target_rgb, tolerance=10, region=None):
        """Trouve la première occurrence d'une couleur

        Args:
            image: PIL.Image ou numpy.ndarray
            target_rgb: Tuple (r, g, b) à chercher
            tolerance: Tolérance par composante
            region: Région optionnelle (x, y, width, height)

        Returns:
            Tuple (x, y) ou None: Position du premier pixel trouvé
        """
        img_array = self._to_numpy_rgb(image)

        # Appliquer la région si spécifiée
        offset_x, offset_y = 0, 0
        if region:
            x, y, w, h = region
            offset_x, offset_y = x, y
            img_array = img_array[y : y + h, x : x + w]

        # Calculer la distance de couleur
        target = np.array(target_rgb)
        diff = np.abs(img_array.astype(np.int16) - target)

        # Trouver les pixels qui correspondent (toutes les composantes <= tolerance)
        matches = np.all(diff <= tolerance, axis=2)

        # Trouver le premier match
        positions = np.where(matches)

        if len(positions[0]) > 0:
            y_found = positions[0][0] + offset_y
            x_found = positions[1][0] + offset_x
            return (x_found, y_found)

        return None

    def find_all_colors(self, image, target_rgb, tolerance=10, region=None, max_results=100):
        """Trouve toutes les occurrences d'une couleur

        Args:
            image: PIL.Image ou numpy.ndarray
            target_rgb: Tuple (r, g, b) à chercher
            tolerance: Tolérance par composante
            region: Région optionnelle (x, y, width, height)
            max_results: Nombre maximum de résultats

        Returns:
            List[Tuple]: Liste de (x, y)
        """
        img_array = self._to_numpy_rgb(image)

        offset_x, offset_y = 0, 0
        if region:
            x, y, w, h = region
            offset_x, offset_y = x, y
            img_array = img_array[y : y + h, x : x + w]

        target = np.array(target_rgb)
        diff = np.abs(img_array.astype(np.int16) - target)
        matches = np.all(diff <= tolerance, axis=2)

        positions = np.where(matches)

        results = []
        for i in range(min(len(positions[0]), max_results)):
            y_found = positions[0][i] + offset_y
            x_found = positions[1][i] + offset_x
            results.append((x_found, y_found))

        return results

    def count_color_in_region(self, image, region, target_rgb, tolerance=10):
        """Compte le nombre de pixels d'une couleur dans une région

        Args:
            image: PIL.Image ou numpy.ndarray
            region: Tuple (x, y, width, height)
            target_rgb: Tuple (r, g, b)
            tolerance: Tolérance

        Returns:
            int: Nombre de pixels correspondants
        """
        img_array = self._to_numpy_rgb(image)

        x, y, w, h = region
        region_img = img_array[y : y + h, x : x + w]

        target = np.array(target_rgb)
        diff = np.abs(region_img.astype(np.int16) - target)
        matches = np.all(diff <= tolerance, axis=2)

        return int(np.sum(matches))

    def get_dominant_color(self, image, region=None, ignore_colors=None):
        """Trouve la couleur dominante d'une image ou région

        Args:
            image: PIL.Image ou numpy.ndarray
            region: Région optionnelle (x, y, width, height)
            ignore_colors: Liste de couleurs à ignorer [(r,g,b), ...]

        Returns:
            Tuple (r, g, b): Couleur dominante
        """
        img_array = self._to_numpy_rgb(image)

        if region:
            x, y, w, h = region
            img_array = img_array[y : y + h, x : x + w]

        # Aplatir l'image en liste de pixels
        pixels = img_array.reshape(-1, 3)

        # Ignorer certaines couleurs si spécifié
        if ignore_colors:
            for color in ignore_colors:
                mask = ~np.all(np.abs(pixels - np.array(color)) < 10, axis=1)
                pixels = pixels[mask]

        if len(pixels) == 0:
            return None

        # Calculer la couleur moyenne (simple)
        mean_color = np.mean(pixels, axis=0).astype(int)

        return tuple(mean_color)

    def color_percentage(self, image, target_rgb, tolerance=10, region=None):
        """Calcule le pourcentage de pixels d'une couleur

        Args:
            image: PIL.Image ou numpy.ndarray
            target_rgb: Tuple (r, g, b)
            tolerance: Tolérance
            region: Région optionnelle

        Returns:
            float: Pourcentage (0-100)
        """
        img_array = self._to_numpy_rgb(image)

        if region:
            x, y, w, h = region
            img_array = img_array[y : y + h, x : x + w]

        total_pixels = img_array.shape[0] * img_array.shape[1]

        target = np.array(target_rgb)
        diff = np.abs(img_array.astype(np.int16) - target)
        matches = np.all(diff <= tolerance, axis=2)

        count = int(np.sum(matches))

        return (count / total_pixels) * 100


# Instance globale
_color_detector_instance = None


def get_color_detector():
    """Retourne une instance singleton de ColorDetector

    Returns:
        ColorDetector: Instance partagée
    """
    global _color_detector_instance
    if _color_detector_instance is None:
        _color_detector_instance = ColorDetector()
    return _color_detector_instance
