# -*- coding: utf-8 -*-
"""Template matching avec OpenCV"""
import cv2
import numpy as np
from PIL import Image
from pathlib import Path

from utils.config import DEFAULT_IMAGE_THRESHOLD
from utils.logger import get_module_logger

logger = get_module_logger("ImageMatcher")


class ImageMatcher:
    """Recherche d'images templates dans des screenshots
    
    Utilise OpenCV pour le template matching.
    """
    
    def __init__(self, default_threshold=None):
        """
        Args:
            default_threshold: Seuil de confiance par défaut (0-1)
        """
        self.default_threshold = default_threshold or DEFAULT_IMAGE_THRESHOLD
        self._template_cache = {}  # Cache des templates chargés
    
    def _load_template(self, template_path):
        """Charge un template depuis le cache ou le fichier (PROTÉGÉ)
        
        Args:
            template_path: Chemin vers l'image template
            
        Returns:
            numpy.ndarray: Template en BGR
            
        Raises:
            FileNotFoundError: Si le template n'existe pas
        """
        template_path = str(template_path)
        
        if template_path not in self._template_cache:
            if not Path(template_path).exists():
                raise FileNotFoundError(f"Template non trouvé: {template_path}")
            
            template = cv2.imread(template_path)
            if template is None:
                raise ValueError(f"Impossible de charger le template: {template_path}")
            
            self._template_cache[template_path] = template
            logger.debug(f"Template chargé: {template_path}")
        
        return self._template_cache[template_path]
    
    def _to_cv2(self, image):
        """Convertit une image en format OpenCV BGR (PROTÉGÉ)
        
        Args:
            image: PIL.Image ou numpy.ndarray
            
        Returns:
            numpy.ndarray: Image en BGR
        """
        if isinstance(image, Image.Image):
            # PIL → numpy RGB → BGR
            img_array = np.array(image)
            return cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        elif isinstance(image, np.ndarray):
            # Vérifier si déjà en BGR ou en RGB
            if len(image.shape) == 3 and image.shape[2] == 3:
                return image  # Supposer déjà en BGR
            return image
        else:
            raise TypeError(f"Type d'image non supporté: {type(image)}")
    
    def find_template(self, screenshot, template_path, threshold=None):
        """Cherche un template dans un screenshot
        
        Args:
            screenshot: PIL.Image ou numpy.ndarray
            template_path: Chemin vers l'image template
            threshold: Seuil de confiance (0-1), utilise default si None
            
        Returns:
            Tuple (x, y, confidence) ou None: Position du centre + confiance
        """
        threshold = threshold if threshold is not None else self.default_threshold
        
        # Vérifier d'abord si le template existe (silencieux si absent)
        if not Path(template_path).exists():
            logger.debug(f"Template non disponible: {Path(template_path).name}")
            return None
        
        try:
            # Charger le template
            template = self._load_template(template_path)
            
            # Convertir le screenshot
            screenshot_bgr = self._to_cv2(screenshot)
            
            # Template matching
            result = cv2.matchTemplate(screenshot_bgr, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= threshold:
                # Calculer le centre
                h, w = template.shape[:2]
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                
                logger.debug(
                    f"Template trouvé: {Path(template_path).name} "
                    f"à ({center_x}, {center_y}) conf={max_val:.2f}"
                )
                return (center_x, center_y, max_val)
            
            logger.debug(
                f"Template non trouvé: {Path(template_path).name} "
                f"(meilleur score: {max_val:.2f} < {threshold})"
            )
            return None
            
        except Exception as e:
            logger.debug(f"Erreur find_template {Path(template_path).name}: {e}")
            return None
    
    def find_all_templates(self, screenshot, template_path, threshold=None, min_distance=10):
        """Trouve toutes les occurrences d'un template
        
        Args:
            screenshot: PIL.Image ou numpy.ndarray
            template_path: Chemin vers l'image template
            threshold: Seuil de confiance (0-1)
            min_distance: Distance minimale entre deux détections (évite doublons)
            
        Returns:
            List[Tuple]: Liste de (x, y, confidence)
        """
        threshold = threshold if threshold is not None else self.default_threshold
        
        try:
            template = self._load_template(template_path)
            screenshot_bgr = self._to_cv2(screenshot)
            
            result = cv2.matchTemplate(screenshot_bgr, template, cv2.TM_CCOEFF_NORMED)
            
            # Trouver toutes les positions > threshold
            locations = np.where(result >= threshold)
            
            h, w = template.shape[:2]
            matches = []
            
            for pt in zip(*locations[::-1]):  # [::-1] pour avoir (x, y) au lieu de (y, x)
                center_x = pt[0] + w // 2
                center_y = pt[1] + h // 2
                confidence = result[pt[1], pt[0]]
                
                # Vérifier la distance avec les matches existants
                is_duplicate = False
                for mx, my, _ in matches:
                    if abs(center_x - mx) < min_distance and abs(center_y - my) < min_distance:
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    matches.append((center_x, center_y, float(confidence)))
            
            # Trier par confiance décroissante
            matches.sort(key=lambda x: x[2], reverse=True)
            
            logger.debug(
                f"find_all_templates: {Path(template_path).name} → {len(matches)} occurrence(s)"
            )
            return matches
            
        except Exception as e:
            logger.error(f"Erreur find_all_templates: {e}")
            return []
    
    def template_exists(self, screenshot, template_path, threshold=None):
        """Vérifie si un template existe dans le screenshot
        
        Args:
            screenshot: PIL.Image ou numpy.ndarray
            template_path: Chemin vers l'image template
            threshold: Seuil de confiance (0-1)
            
        Returns:
            bool: True si trouvé
        """
        return self.find_template(screenshot, template_path, threshold) is not None
    
    def find_template_multiscale(self, screenshot, template_path, threshold=None,
                                  scales=None, return_scale=False):
        """Cherche un template à plusieurs échelles

        Teste le template à différentes échelles pour gérer les variations de résolution.

        Args:
            screenshot: PIL.Image ou numpy.ndarray
            template_path: Chemin vers l'image template
            threshold: Seuil de confiance (0-1)
            scales: Liste d'échelles à tester (défaut: [0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3])
            return_scale: Si True, retourne aussi l'échelle trouvée

        Returns:
            Tuple (x, y, confidence) ou (x, y, confidence, scale) si return_scale=True
            None si non trouvé
        """
        threshold = threshold if threshold is not None else self.default_threshold
        scales = scales or [0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3]

        if not Path(template_path).exists():
            logger.debug(f"Template non disponible: {Path(template_path).name}")
            return None

        try:
            # Charger le template original
            template_orig = self._load_template(template_path)
            screenshot_bgr = self._to_cv2(screenshot)

            best_match = None
            best_confidence = 0
            best_scale = 1.0

            # Tester chaque échelle
            for scale in scales:
                # Redimensionner le template
                h, w = template_orig.shape[:2]
                new_w = int(w * scale)
                new_h = int(h * scale)

                # Vérifier que le template redimensionné n'est pas plus grand que le screenshot
                if new_w > screenshot_bgr.shape[1] or new_h > screenshot_bgr.shape[0]:
                    continue

                template_resized = cv2.resize(template_orig, (new_w, new_h))

                # Template matching
                result = cv2.matchTemplate(screenshot_bgr, template_resized, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

                # Si c'est le meilleur score jusqu'à présent
                if max_val > best_confidence:
                    best_confidence = max_val
                    best_scale = scale

                    # Calculer le centre
                    center_x = max_loc[0] + new_w // 2
                    center_y = max_loc[1] + new_h // 2
                    best_match = (center_x, center_y, max_val)

            # Vérifier si le meilleur match dépasse le seuil
            if best_match and best_confidence >= threshold:
                logger.debug(
                    f"Template trouvé (multi-échelle): {Path(template_path).name} "
                    f"à {best_match[:2]} conf={best_confidence:.2f} échelle={best_scale:.2f}"
                )

                if return_scale:
                    return best_match + (best_scale,)
                return best_match

            logger.debug(
                f"Template non trouvé (multi-échelle): {Path(template_path).name} "
                f"(meilleur score: {best_confidence:.2f} à échelle {best_scale:.2f})"
            )
            return None

        except Exception as e:
            logger.debug(f"Erreur find_template_multiscale {Path(template_path).name}: {e}")
            return None

    def clear_cache(self):
        """Vide le cache des templates"""
        self._template_cache.clear()
        logger.debug("Cache des templates vidé")

    def preload_templates(self, template_paths):
        """Précharge une liste de templates dans le cache
        
        Args:
            template_paths: Liste de chemins de templates
        """
        for path in template_paths:
            try:
                self._load_template(path)
            except Exception as e:
                logger.warning(f"Impossible de précharger {path}: {e}")


# Instance globale
_image_matcher_instance = None


def get_image_matcher():
    """Retourne une instance singleton de ImageMatcher
    
    Returns:
        ImageMatcher: Instance partagée
    """
    global _image_matcher_instance
    if _image_matcher_instance is None:
        _image_matcher_instance = ImageMatcher()
    return _image_matcher_instance
