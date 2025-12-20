# -*- coding: utf-8 -*-
"""Capture d'écran par région (compatible BlueStacks)

Note: La capture par handle (hwnd) peut retourner un écran noir avec BlueStacks
car il utilise DirectX/OpenGL. On utilise donc la capture par région d'écran
après avoir activé la fenêtre.
"""
import mss
import mss.tools
from PIL import Image
import numpy as np

from utils.logger import get_module_logger

logger = get_module_logger("ScreenCapture")


class ScreenCapture:
    """Capture d'écran par région
    
    Utilise mss pour des captures rapides.
    La fenêtre doit être au premier plan et visible.
    """
    
    def __init__(self):
        """Initialise le capturer mss"""
        self._sct = None
    
    @property
    def sct(self):
        """Lazy initialization du capturer mss"""
        if self._sct is None:
            self._sct = mss.mss()
        return self._sct
    
    def capture_region(self, x, y, width, height):
        """Capture une région spécifique de l'écran
        
        Args:
            x: Coordonnée X du coin supérieur gauche
            y: Coordonnée Y du coin supérieur gauche
            width: Largeur de la région
            height: Hauteur de la région
            
        Returns:
            PIL.Image: Image capturée en RGB
        """
        monitor = {
            "left": x,
            "top": y,
            "width": width,
            "height": height
        }
        
        try:
            screenshot = self.sct.grab(monitor)
            # Convertir en PIL Image RGB (mss retourne BGRA)
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            return img
        except Exception as e:
            logger.error(f"Erreur capture région ({x}, {y}, {width}, {height}): {e}")
            return None
    
    def capture_window_region(self, window_rect, region=None):
        """Capture une fenêtre (ou une sous-région de celle-ci)
        
        Args:
            window_rect: Tuple (left, top, right, bottom) de la fenêtre
            region: Sous-région optionnelle (x_rel, y_rel, width, height)
                    relative au coin supérieur gauche de la fenêtre
            
        Returns:
            PIL.Image: Image capturée en RGB
        """
        left, top, right, bottom = window_rect
        window_width = right - left
        window_height = bottom - top
        
        if region:
            # Région relative à la fenêtre
            x_rel, y_rel, width, height = region
            x_abs = left + x_rel
            y_abs = top + y_rel
            # Contraindre aux limites de la fenêtre
            width = min(width, window_width - x_rel)
            height = min(height, window_height - y_rel)
        else:
            # Toute la fenêtre
            x_abs = left
            y_abs = top
            width = window_width
            height = window_height
        
        return self.capture_region(x_abs, y_abs, width, height)
    
    def capture_full_screen(self, monitor_index=0):
        """Capture l'écran complet
        
        Args:
            monitor_index: Index du moniteur (0 = principal)
            
        Returns:
            PIL.Image: Image de l'écran complet
        """
        try:
            # mss.monitors[0] = tous les écrans combinés
            # mss.monitors[1] = premier écran, etc.
            monitors = self.sct.monitors
            
            if monitor_index + 1 >= len(monitors):
                logger.warning(f"Moniteur {monitor_index} non trouvé, utilisation du principal")
                monitor_index = 0
            
            monitor = monitors[monitor_index + 1]  # +1 car index 0 = tous les écrans
            screenshot = self.sct.grab(monitor)
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            return img
        except Exception as e:
            logger.error(f"Erreur capture écran complet: {e}")
            return None
    
    def save_capture(self, image, filepath):
        """Sauvegarde une capture dans un fichier
        
        Args:
            image: PIL.Image à sauvegarder
            filepath: Chemin du fichier de sortie
            
        Returns:
            bool: True si succès
        """
        try:
            image.save(str(filepath))
            logger.debug(f"Capture sauvegardée: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Erreur sauvegarde capture: {e}")
            return False
    
    def to_numpy(self, image):
        """Convertit une PIL.Image en numpy array (pour OpenCV)
        
        Args:
            image: PIL.Image
            
        Returns:
            numpy.ndarray: Image en format BGR (pour OpenCV)
        """
        if image is None:
            return None
        
        # Convertir PIL → numpy RGB
        img_array = np.array(image)
        
        # Convertir RGB → BGR pour OpenCV
        img_bgr = img_array[:, :, ::-1].copy()
        
        return img_bgr
    
    def close(self):
        """Ferme le capturer mss"""
        if self._sct is not None:
            self._sct.close()
            self._sct = None
    
    def __del__(self):
        """Destructeur"""
        self.close()


# Instance globale pour réutilisation
_screen_capture_instance = None


def get_screen_capture():
    """Retourne une instance singleton de ScreenCapture
    
    Returns:
        ScreenCapture: Instance partagée
    """
    global _screen_capture_instance
    if _screen_capture_instance is None:
        _screen_capture_instance = ScreenCapture()
    return _screen_capture_instance
