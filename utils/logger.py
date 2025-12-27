# -*- coding: utf-8 -*-
"""Système de logging multi-niveaux"""
import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
from pathlib import Path

from utils.config import (
    LOGS_DIR,
    LOG_LEVEL_CONSOLE,
    LOG_ROTATION_SIZE_MB,
    LOG_BACKUP_COUNT,
)


# Logger racine configuré
_root_logger_configured = False


class ShortNameFilter(logging.Filter):
    """Filtre qui ajoute 'shortname' aux logs pour un affichage plus lisible"""

    def filter(self, record):
        # Extraire le nom court depuis le nom complet du logger
        # Ex: 'automation_framework.Engine' -> 'Engine'
        # Ex: 'automation_framework.ManoirPrincipal' -> 'ManoirPrincipal'
        # Ex: 'automation_framework.ActionAttendre' -> 'ActionAttendre'
        if '.' in record.name:
            record.shortname = record.name.split('.')[-1]
        else:
            record.shortname = record.name
        return True


def setup_logging(level=None):
    """Configure le logging global de l'application
    
    Args:
        level: Niveau de log pour la console (optionnel, utilise config sinon)
        
    Returns:
        logging.Logger: Logger principal configuré
    """
    global _root_logger_configured
    
    # Éviter double configuration
    if _root_logger_configured:
        return logging.getLogger('automation_framework')
    
    # Niveau de log
    if level is None:
        # Utiliser le niveau de la config
        level = getattr(logging, LOG_LEVEL_CONSOLE.upper(), logging.DEBUG)
    elif isinstance(level, str):
        level = getattr(logging, level.upper(), logging.DEBUG)
    
    # Logger racine
    logger = logging.getLogger('automation_framework')
    logger.setLevel(logging.DEBUG)
    
    # Format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Format console (avec nom du composant)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(shortname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # ===== CONSOLE HANDLER =====
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(console_formatter)
    console_handler.addFilter(ShortNameFilter())
    logger.addHandler(console_handler)
    
    # ===== ERREURS GLOBALES (fichier) =====
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    error_handler = RotatingFileHandler(
        LOGS_DIR / 'errors.log',
        maxBytes=LOG_ROTATION_SIZE_MB * 1024 * 1024,
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    
    # ===== LOG GÉNÉRAL (fichier) =====
    general_handler = RotatingFileHandler(
        LOGS_DIR / 'automation.log',
        maxBytes=LOG_ROTATION_SIZE_MB * 1024 * 1024,
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    general_handler.setLevel(logging.INFO)
    general_handler.setFormatter(formatter)
    logger.addHandler(general_handler)
    
    _root_logger_configured = True
    
    logger.info("=" * 60)
    logger.info("Système de logging initialisé")
    logger.info("=" * 60)
    
    return logger


def get_manoir_logger(nom_manoir):
    """Crée un logger spécifique pour un manoir

    Args:
        nom_manoir: Nom de la classe de manoir

    Returns:
        logging.Logger: Logger configuré pour ce manoir
    """
    logger_name = f'automation_framework.{nom_manoir}'
    logger = logging.getLogger(logger_name)

    # Si déjà configuré, retourner directement
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Format
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # ===== FICHIER DEBUG PAR MANOIR =====
    log_dir = LOGS_DIR / f'manoir_{nom_manoir}'
    log_dir.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now().strftime('%Y%m%d')
    debug_handler = RotatingFileHandler(
        log_dir / f'debug_{date_str}.log',
        maxBytes=LOG_ROTATION_SIZE_MB * 1024 * 1024,
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(formatter)
    logger.addHandler(debug_handler)

    # Propager au logger parent (pour que les erreurs remontent)
    logger.propagate = True

    return logger


def get_module_logger(module_name, level=None):
    """Crée un logger pour un module (Engine, RecoveryManager, etc.)

    Args:
        module_name: Nom du module
        level: Niveau de log optionnel (str ou int)

    Returns:
        logging.Logger: Logger configuré pour ce module
    """
    logger_name = f'automation_framework.{module_name}'
    logger = logging.getLogger(logger_name)

    # Appliquer le niveau si spécifié
    if level is not None:
        if isinstance(level, str):
            level = getattr(logging, level.upper(), logging.DEBUG)
        logger.setLevel(level)

    # Hérite de la config du logger parent
    logger.propagate = True

    return logger


def get_action_logger(action_class_name):
    """Crée un logger pour une action

    Args:
        action_class_name: Nom de la classe d'action (ex: 'ActionAttendre')

    Returns:
        logging.Logger: Logger configuré pour cette action
    """
    logger_name = f'automation_framework.{action_class_name}'
    logger = logging.getLogger(logger_name)

    # Hérite de la config du logger parent
    logger.propagate = True

    return logger
