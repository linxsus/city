# -*- coding: utf-8 -*-
"""Conversion et manipulation de coordonnées"""


def relative_to_absolute(x_rel, y_rel, window_rect):
    """Convertit des coordonnées relatives (dans la fenêtre) en absolues (écran)
    
    Args:
        x_rel: Coordonnée X relative à la fenêtre
        y_rel: Coordonnée Y relative à la fenêtre
        window_rect: Tuple (left, top, right, bottom) de la fenêtre
        
    Returns:
        Tuple (x_abs, y_abs): Coordonnées absolues sur l'écran
    """
    left, top, right, bottom = window_rect
    x_abs = left + x_rel
    y_abs = top + y_rel
    return (x_abs, y_abs)


def absolute_to_relative(x_abs, y_abs, window_rect):
    """Convertit des coordonnées absolues (écran) en relatives (fenêtre)
    
    Args:
        x_abs: Coordonnée X absolue sur l'écran
        y_abs: Coordonnée Y absolue sur l'écran
        window_rect: Tuple (left, top, right, bottom) de la fenêtre
        
    Returns:
        Tuple (x_rel, y_rel): Coordonnées relatives à la fenêtre
    """
    left, top, right, bottom = window_rect
    x_rel = x_abs - left
    y_rel = y_abs - top
    return (x_rel, y_rel)


def get_window_size(window_rect):
    """Calcule la taille d'une fenêtre à partir de son rectangle
    
    Args:
        window_rect: Tuple (left, top, right, bottom)
        
    Returns:
        Tuple (width, height): Dimensions de la fenêtre
    """
    left, top, right, bottom = window_rect
    width = right - left
    height = bottom - top
    return (width, height)


def get_window_center(window_rect):
    """Calcule le centre d'une fenêtre
    
    Args:
        window_rect: Tuple (left, top, right, bottom)
        
    Returns:
        Tuple (x_center, y_center): Centre de la fenêtre (coordonnées absolues)
    """
    left, top, right, bottom = window_rect
    x_center = (left + right) // 2
    y_center = (top + bottom) // 2
    return (x_center, y_center)


def is_point_in_window(x, y, window_rect):
    """Vérifie si un point est à l'intérieur d'une fenêtre
    
    Args:
        x, y: Coordonnées absolues du point
        window_rect: Tuple (left, top, right, bottom)
        
    Returns:
        bool: True si le point est dans la fenêtre
    """
    left, top, right, bottom = window_rect
    return left <= x <= right and top <= y <= bottom


def region_to_absolute(region_rel, window_rect):
    """Convertit une région relative en région absolue
    
    Args:
        region_rel: Tuple (x, y, width, height) relatif à la fenêtre
        window_rect: Tuple (left, top, right, bottom) de la fenêtre
        
    Returns:
        Tuple (x_abs, y_abs, width, height): Région en coordonnées absolues
    """
    x_rel, y_rel, width, height = region_rel
    left, top, right, bottom = window_rect
    x_abs = left + x_rel
    y_abs = top + y_rel
    return (x_abs, y_abs, width, height)


def clamp_to_window(x, y, window_rect):
    """Contraint un point à rester dans les limites de la fenêtre
    
    Args:
        x, y: Coordonnées du point
        window_rect: Tuple (left, top, right, bottom)
        
    Returns:
        Tuple (x_clamped, y_clamped): Point contraint
    """
    left, top, right, bottom = window_rect
    x_clamped = max(left, min(x, right))
    y_clamped = max(top, min(y, bottom))
    return (x_clamped, y_clamped)
