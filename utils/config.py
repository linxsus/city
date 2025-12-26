# -*- coding: utf-8 -*-
"""Configuration globale de l'application"""
import os
from pathlib import Path


# =====================================================
# CHEMINS
# =====================================================

# Chemin de base du projet (détecté automatiquement)
# utils/config.py -> parent = utils -> parent = racine du projet
BASE_DIR = Path(__file__).parent.parent

# Sous-dossiers
TEMPLATES_DIR = BASE_DIR / "templates"
LOGS_DIR = BASE_DIR / "logs"
CAPTURES_DIR = LOGS_DIR / "captures"
DATA_DIR = BASE_DIR / "data"
RACCOURCIS_DIR = BASE_DIR / "raccourcis"
CONFIG_DIR = BASE_DIR / "config"

# Sous-dossiers templates
TEMPLATES_POPUPS_DIR = TEMPLATES_DIR / "popups"
TEMPLATES_BOUTONS_DIR = TEMPLATES_DIR / "boutons"

# Fichiers de données persistées
TIMERS_FILE = DATA_DIR / "timers.json"
SLOTS_FILE = DATA_DIR / "slots.json"
WINDOW_STATES_FILE = DATA_DIR / "window_states.json"
BOUCLES_STATE_FILE = DATA_DIR / "boucles_state.json"
RACCOURCIS_CONFIG_FILE = RACCOURCIS_DIR / "config_raccourcis.json"


# =====================================================
# TIMEOUTS ET DÉLAIS
# =====================================================

# Temps maximum par fenêtre avant de passer à la suivante (secondes)
DEFAULT_TIMEOUT_FENETRE = 60

# Délai de pause entre les fenêtres (secondes)
DELAI_ENTRE_FENETRES = 0

# Pause si activité utilisateur détectée (secondes)
PAUSE_SI_ACTIVITE_USER = 180

# Pause entre chaque action (secondes)
PAUSE_ENTRE_ACTIONS = 0

# Pause entre chaque fenêtre (secondes)
PAUSE_ENTRE_FENETRES = 1.0

# Pause quand utilisateur actif (secondes)
PAUSE_UTILISATEUR_ACTIF = 5.0

# Temps d'inactivité requis avant de reprendre (secondes)
TEMPS_INACTIVITE_REQUIS = 0.5  # Réduit pour tests


# =====================================================
# DÉTECTION VISUELLE
# =====================================================

# Seuil de confiance pour le template matching (0-1)
DEFAULT_IMAGE_THRESHOLD = 0.8

# Langues OCR (format EasyOCR : 2 lettres)
OCR_LANGUAGES = ['fr', 'en']

# Utiliser EasyOCR (True) ou Tesseract (False)
USE_EASYOCR = True

# Chemin vers l'exécutable Tesseract (Windows)
# Mettre None pour utiliser le PATH système
TESSERACT_CMD = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


# =====================================================
# DÉTECTION ACTIVITÉ UTILISATEUR
# =====================================================

# Seuil de mouvement souris pour détecter activité (pixels)
MOUSE_MOVE_THRESHOLD = 5

# Intervalle entre vérifications d'activité (secondes)
ACTIVITY_CHECK_INTERVAL = 1.0


# =====================================================
# LOGGING
# =====================================================

# Niveau de log console : DEBUG, INFO, WARNING, ERROR
LOG_LEVEL_CONSOLE = 'DEBUG'

# Taille max d'un fichier log avant rotation (Mo)
LOG_ROTATION_SIZE_MB = 50

# Nombre de fichiers backup à conserver
LOG_BACKUP_COUNT = 10


# =====================================================
# CAPTURE D'ÉCRAN
# =====================================================

# Format des screenshots
CAPTURE_FORMAT = 'PNG'

# Qualité JPEG si utilisé (0-100)
CAPTURE_QUALITY = 85


# =====================================================
# RÉCUPÉRATION / GESTION ERREURS
# =====================================================

# Temps d'exclusion si "Compte utilisé ailleurs" (secondes)
EXCLUSION_COMPTE_UTILISE = 2 * 60 * 60  # 2 heures

# Temps d'exclusion après relance BlueStacks (secondes)
EXCLUSION_RELANCE_BLUESTACKS = 10 * 60  # 10 minutes

# Temps d'attente après lancement jeu (secondes)
ATTENTE_LANCEMENT_JEU = 60


# =====================================================
# INITIALISATION DES DOSSIERS
# =====================================================

def init_directories():
    """Crée les dossiers nécessaires s'ils n'existent pas"""
    directories = [
        TEMPLATES_DIR,
        TEMPLATES_POPUPS_DIR,
        TEMPLATES_BOUTONS_DIR,
        LOGS_DIR,
        CAPTURES_DIR,
        DATA_DIR,
        RACCOURCIS_DIR,
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


# Créer les dossiers au chargement du module
init_directories()
