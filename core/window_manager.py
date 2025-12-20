# -*- coding: utf-8 -*-
"""Gestion des fenêtres Windows

Utilise pywin32 pour interagir avec les fenêtres Windows.
Fonctionne uniquement sur Windows.
"""
import time

from utils.logger import get_module_logger

logger = get_module_logger("WindowManager")

# Import conditionnel pour Windows
try:
    import win32gui
    import win32con
    import win32process
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    logger.warning("pywin32 non disponible - WindowManager désactivé")


class WindowManager:
    """Gestionnaire de fenêtres Windows
    
    Permet de trouver, activer et manipuler les fenêtres Windows.
    """
    
    def __init__(self):
        """Initialise le gestionnaire"""
        if not WIN32_AVAILABLE:
            logger.error("pywin32 requis pour WindowManager")
        
        # Cache des fenêtres trouvées {titre: hwnd}
        self._window_cache = {}
    
    def find_window(self, titre_partiel, use_cache=True):
        """Trouve une fenêtre par son titre (recherche partielle)
        
        Args:
            titre_partiel: Partie du titre à chercher (insensible à la casse)
            use_cache: Utiliser le cache si disponible
            
        Returns:
            int ou None: Handle de la fenêtre (hwnd)
        """
        if not WIN32_AVAILABLE:
            return None
        
        # Vérifier le cache
        if use_cache and titre_partiel in self._window_cache:
            hwnd = self._window_cache[titre_partiel]
            # Vérifier que la fenêtre existe toujours
            if win32gui.IsWindow(hwnd):
                return hwnd
            else:
                del self._window_cache[titre_partiel]
        
        # Rechercher la fenêtre
        found_windows = []
        
        def enum_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                titre = win32gui.GetWindowText(hwnd)
                if titre and titre_partiel.lower() in titre.lower():
                    windows.append((hwnd, titre))
        
        try:
            win32gui.EnumWindows(enum_callback, found_windows)
        except Exception as e:
            logger.error(f"Erreur EnumWindows: {e}")
            return None
        
        if found_windows:
            hwnd, titre = found_windows[0]
            self._window_cache[titre_partiel] = hwnd
            logger.debug(f"Fenêtre trouvée: '{titre}' (hwnd={hwnd})")
            return hwnd
        
        logger.debug(f"Fenêtre non trouvée: '{titre_partiel}'")
        return None
    
    def find_all_windows(self, titre_partiel):
        """Trouve toutes les fenêtres correspondant au titre
        
        Args:
            titre_partiel: Partie du titre à chercher
            
        Returns:
            List[Tuple]: Liste de (hwnd, titre_complet)
        """
        if not WIN32_AVAILABLE:
            return []
        
        found_windows = []
        
        def enum_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                titre = win32gui.GetWindowText(hwnd)
                if titre and titre_partiel.lower() in titre.lower():
                    windows.append((hwnd, titre))
        
        try:
            win32gui.EnumWindows(enum_callback, found_windows)
        except Exception as e:
            logger.error(f"Erreur EnumWindows: {e}")
        
        logger.debug(f"Trouvé {len(found_windows)} fenêtre(s) pour '{titre_partiel}'")
        return found_windows
    
    def activate_window(self, hwnd):
        """Active une fenêtre (met au premier plan)
        
        Args:
            hwnd: Handle de la fenêtre
            
        Returns:
            bool: True si succès
        """
        if not WIN32_AVAILABLE:
            return False
        
        try:
            # Vérifier que la fenêtre existe
            if not win32gui.IsWindow(hwnd):
                logger.error(f"Fenêtre {hwnd} n'existe plus")
                return False
            
            # Restaurer si minimisée
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                time.sleep(0.2)
            
            # Mettre au premier plan
            # Méthode robuste avec AttachThreadInput pour contourner restrictions Windows
            try:
                # Obtenir le thread de la fenêtre courante au premier plan
                foreground_hwnd = win32gui.GetForegroundWindow()
                foreground_thread = win32process.GetWindowThreadProcessId(foreground_hwnd)[0]
                target_thread = win32process.GetWindowThreadProcessId(hwnd)[0]

                # Attacher les threads pour permettre SetForegroundWindow
                if foreground_thread != target_thread:
                    try:
                        import ctypes
                        ctypes.windll.user32.AttachThreadInput(foreground_thread, target_thread, True)
                    except:
                        pass  # Ignorer si échoue

                # Forcer l'activation
                win32gui.BringWindowToTop(hwnd)
                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                win32gui.SetForegroundWindow(hwnd)

                # Détacher les threads
                if foreground_thread != target_thread:
                    try:
                        ctypes.windll.user32.AttachThreadInput(foreground_thread, target_thread, False)
                    except:
                        pass

            except Exception as e:
                # Fallback : méthode simple
                try:
                    win32gui.BringWindowToTop(hwnd)
                    win32gui.SetForegroundWindow(hwnd)
                except:
                    pass

            time.sleep(0.1)
            
            logger.debug(f"Fenêtre {hwnd} activée")
            return True
            
        except Exception as e:
            # SetForegroundWindow peut échouer si l'utilisateur est actif
            # Ce n'est pas critique, juste un warning
            logger.warning(f"Activation fenêtre {hwnd} partielle: {e}")
            return True  # On continue quand même
    
    def get_window_rect(self, hwnd):
        """Obtient les coordonnées d'une fenêtre
        
        Args:
            hwnd: Handle de la fenêtre
            
        Returns:
            Tuple (left, top, right, bottom) ou None
        """
        if not WIN32_AVAILABLE:
            return None
        
        try:
            return win32gui.GetWindowRect(hwnd)
        except Exception as e:
            logger.error(f"Erreur GetWindowRect({hwnd}): {e}")
            return None
    
    def get_window_size(self, hwnd):
        """Obtient la taille d'une fenêtre
        
        Args:
            hwnd: Handle de la fenêtre
            
        Returns:
            Tuple (width, height) ou None
        """
        rect = self.get_window_rect(hwnd)
        if rect:
            left, top, right, bottom = rect
            return (right - left, bottom - top)
        return None
    
    def get_window_title(self, hwnd):
        """Obtient le titre d'une fenêtre
        
        Args:
            hwnd: Handle de la fenêtre
            
        Returns:
            str ou None: Titre de la fenêtre
        """
        if not WIN32_AVAILABLE:
            return None
        
        try:
            return win32gui.GetWindowText(hwnd)
        except Exception:
            return None
    
    def is_window_visible(self, hwnd):
        """Vérifie si une fenêtre est visible
        
        Args:
            hwnd: Handle de la fenêtre
            
        Returns:
            bool: True si visible
        """
        if not WIN32_AVAILABLE:
            return False
        
        try:
            return win32gui.IsWindowVisible(hwnd)
        except Exception:
            return False
    
    def is_window_minimized(self, hwnd):
        """Vérifie si une fenêtre est minimisée
        
        Args:
            hwnd: Handle de la fenêtre
            
        Returns:
            bool: True si minimisée
        """
        if not WIN32_AVAILABLE:
            return False
        
        try:
            return win32gui.IsIconic(hwnd)
        except Exception:
            return False
    
    def window_exists(self, hwnd):
        """Vérifie si une fenêtre existe
        
        Args:
            hwnd: Handle de la fenêtre
            
        Returns:
            bool: True si existe
        """
        if not WIN32_AVAILABLE:
            return False
        
        try:
            return win32gui.IsWindow(hwnd)
        except Exception:
            return False
    
    def minimize_window(self, hwnd):
        """Minimise une fenêtre
        
        Args:
            hwnd: Handle de la fenêtre
            
        Returns:
            bool: True si succès
        """
        if not WIN32_AVAILABLE:
            return False
        
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
            return True
        except Exception as e:
            logger.error(f"Erreur minimize_window({hwnd}): {e}")
            return False
    
    def restore_window(self, hwnd):
        """Restaure une fenêtre minimisée
        
        Args:
            hwnd: Handle de la fenêtre
            
        Returns:
            bool: True si succès
        """
        if not WIN32_AVAILABLE:
            return False
        
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            return True
        except Exception as e:
            logger.error(f"Erreur restore_window({hwnd}): {e}")
            return False
    
    def close_window(self, hwnd):
        """Ferme une fenêtre (envoie WM_CLOSE)

        Args:
            hwnd: Handle de la fenêtre

        Returns:
            bool: True si message envoyé
        """
        if not WIN32_AVAILABLE:
            return False

        try:
            win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
            logger.info(f"Message WM_CLOSE envoyé à {hwnd}")
            return True
        except Exception as e:
            logger.error(f"Erreur close_window({hwnd}): {e}")
            return False

    def move_and_resize_window(self, hwnd, x=None, y=None, width=None, height=None):
        """Déplace et/ou redimensionne une fenêtre

        Args:
            hwnd: Handle de la fenêtre
            x: Position X (None pour conserver)
            y: Position Y (None pour conserver)
            width: Largeur (None pour conserver)
            height: Hauteur (None pour conserver)

        Returns:
            bool: True si succès
        """
        if not WIN32_AVAILABLE:
            return False

        try:
            # Vérifier que la fenêtre existe
            if not win32gui.IsWindow(hwnd):
                logger.error(f"Fenêtre {hwnd} n'existe plus")
                return False

            # Obtenir les coordonnées actuelles
            current_rect = win32gui.GetWindowRect(hwnd)
            current_x, current_y = current_rect[0], current_rect[1]
            current_width = current_rect[2] - current_rect[0]
            current_height = current_rect[3] - current_rect[1]

            # Utiliser les valeurs actuelles si non spécifiées
            new_x = x if x is not None else current_x
            new_y = y if y is not None else current_y
            new_width = width if width is not None else current_width
            new_height = height if height is not None else current_height

            # Déplacer et redimensionner
            win32gui.MoveWindow(hwnd, new_x, new_y, new_width, new_height, True)

            logger.info(f"Fenêtre {hwnd} placée à ({new_x}, {new_y}) avec dimensions {new_width}x{new_height}")
            return True

        except Exception as e:
            logger.error(f"Erreur move_and_resize_window({hwnd}): {e}")
            return False

    def resize_with_aspect_ratio(self, hwnd, height, aspect_ratio=None, x=None, y=None):
        """Redimensionne une fenêtre en maintenant le ratio largeur/hauteur

        La hauteur est la dimension de référence. La largeur est calculée
        automatiquement selon le ratio.

        Args:
            hwnd: Handle de la fenêtre
            height: Hauteur cible (dimension de référence)
            aspect_ratio: Ratio largeur/hauteur (None pour conserver le ratio actuel)
            x: Position X (None pour conserver)
            y: Position Y (None pour conserver)

        Returns:
            bool: True si succès

        Example:
            # Redimensionner à 600px de hauteur en gardant le ratio actuel
            resize_with_aspect_ratio(hwnd, 600)

            # Redimensionner à 600px de hauteur avec ratio 16:9
            resize_with_aspect_ratio(hwnd, 600, aspect_ratio=16/9)
        """
        if not WIN32_AVAILABLE:
            return False

        try:
            # Vérifier que la fenêtre existe
            if not win32gui.IsWindow(hwnd):
                logger.error(f"Fenêtre {hwnd} n'existe plus")
                return False

            # Obtenir les dimensions actuelles si besoin du ratio
            if aspect_ratio is None:
                current_size = self.get_window_size(hwnd)
                if not current_size:
                    logger.error(f"Impossible d'obtenir les dimensions de {hwnd}")
                    return False
                current_width, current_height = current_size
                if current_height == 0:
                    logger.error(f"Hauteur actuelle nulle pour {hwnd}")
                    return False
                aspect_ratio = current_width / current_height
                logger.debug(f"Ratio actuel détecté: {aspect_ratio:.2f}")

            # Calculer la largeur selon le ratio et la hauteur
            width = int(height * aspect_ratio)

            logger.info(
                f"Redimensionnement avec ratio {aspect_ratio:.2f}: "
                f"{width}x{height} (hauteur={height}, largeur calculée={width})"
            )

            # Utiliser move_and_resize_window pour effectuer le changement
            return self.move_and_resize_window(hwnd, x=x, y=y, width=width, height=height)

        except Exception as e:
            logger.error(f"Erreur resize_with_aspect_ratio({hwnd}): {e}")
            return False
    
    def get_foreground_window(self):
        """Obtient la fenêtre actuellement au premier plan
        
        Returns:
            int: Handle de la fenêtre active
        """
        if not WIN32_AVAILABLE:
            return None
        
        try:
            return win32gui.GetForegroundWindow()
        except Exception:
            return None
    
    def is_window_foreground(self, hwnd):
        """Vérifie si une fenêtre est au premier plan
        
        Args:
            hwnd: Handle de la fenêtre
            
        Returns:
            bool: True si au premier plan
        """
        return self.get_foreground_window() == hwnd
    
    def clear_cache(self):
        """Vide le cache des fenêtres"""
        self._window_cache.clear()
        logger.debug("Cache des fenêtres vidé")
    
    def list_all_windows(self):
        """Liste toutes les fenêtres visibles
        
        Returns:
            List[Tuple]: Liste de (hwnd, titre)
        """
        if not WIN32_AVAILABLE:
            return []
        
        windows = []
        
        def enum_callback(hwnd, result):
            if win32gui.IsWindowVisible(hwnd):
                titre = win32gui.GetWindowText(hwnd)
                if titre:  # Ignorer les fenêtres sans titre
                    result.append((hwnd, titre))
        
        try:
            win32gui.EnumWindows(enum_callback, windows)
        except Exception as e:
            logger.error(f"Erreur list_all_windows: {e}")
        
        return windows


# Instance globale
_window_manager_instance = None


def get_window_manager():
    """Retourne une instance singleton de WindowManager
    
    Returns:
        WindowManager: Instance partagée
    """
    global _window_manager_instance
    if _window_manager_instance is None:
        _window_manager_instance = WindowManager()
    return _window_manager_instance
