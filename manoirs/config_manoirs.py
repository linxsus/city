# -*- coding: utf-8 -*-
"""Configuration des manoirs

Définit la configuration de chaque manoir à automatiser.
Configuration pour tests réels.
"""
from pathlib import Path
from utils.config import RACCOURCIS_DIR


# =====================================================
# CONFIGURATION PAR DÉFAUT
# =====================================================

# Dimensions par défaut de la zone de jeu
LARGEUR_DEFAUT = 1280
HAUTEUR_DEFAUT = 720

# Chemin vers BlueStacks
BLUESTACKS_PLAYER = r"C:\Program Files\BlueStacks_nxt\HD-Player.exe"
BLUESTACKS_MANAGER = r"C:\Program Files\BlueStacks_nxt\HD-MultiInstanceManager.exe"


# =====================================================
# CONFIGURATION DES MANOIRS
# =====================================================

MANOIRS_CONFIG = {
    # Manoir principal - Compte principal avec BlueStacks
    "principal": {
        "nom": "Manoir Principal",
        "titre_bluestacks": "principal",  # Titre de votre fenêtre BlueStacks
        "type": "principal",
        "priorite": 50,
        "largeur": 600,
        "hauteur": 1040,
        # Position de la fenêtre (x, y) - None pour ne pas modifier
        "position_x": 0,
        "position_y": 0,
        # Commande de lancement BlueStacks
        "commande_lancement": [
            BLUESTACKS_PLAYER,
            "--instance", "Nougat32_1",  # Votre instance BlueStacks
            "--cmd", "launchAppWithBsx",
            "--package", "com.yottagames.mafiawar",
            "--source", "desktop_shortcut"
        ],
        # Temps d'attente après lancement (secondes)
        "temps_initialisation": 300,
    },
}

# =====================================================
# HELPERS
# =====================================================

def get_config(manoir_id):
    """Récupère la configuration d'un manoir

    Args:
        manoir_id: ID du manoir

    Returns:
        dict ou None: Configuration
    """
    return MANOIRS_CONFIG.get(manoir_id)


def get_all_manoir_ids():
    """Récupère tous les IDs de manoirs

    Returns:
        List[str]: Liste des IDs
    """
    return list(MANOIRS_CONFIG.keys())


def get_manoirs_par_type(type_manoir):
    """Récupère les IDs des manoirs d'un type donné

    Args:
        type_manoir: Type de manoir ('reel', 'virtuel', 'farm', etc.)

    Returns:
        List[str]: Liste des IDs
    """
    return [
        mid for mid, config in MANOIRS_CONFIG.items()
        if config.get("type") == type_manoir
    ]


def get_farm_ids():
    """Récupère les IDs des farms

    Returns:
        List[str]: Liste des IDs de farms
    """
    return get_manoirs_par_type("farm")


def get_principal_id():
    """Récupère l'ID du compte principal

    Returns:
        str ou None: ID du principal
    """
    ids = get_manoirs_par_type("principal")
    return ids[0] if ids else None


def ajouter_farm(manoir_id, titre_bluestacks, rang, niveau_manoir=15, priorite=None):
    """Ajoute une nouvelle farm à la configuration

    Args:
        manoir_id: ID unique
        titre_bluestacks: Titre de la fenêtre
        rang: Rang de la farm
        niveau_manoir: Niveau du manoir
        priorite: Priorité (auto si None)
    """
    if priorite is None:
        priorite = max(10, 50 - rang * 5)

    MANOIRS_CONFIG[manoir_id] = {
        "nom": f"Farm {rang}",
        "titre_bluestacks": titre_bluestacks,
        "type": "farm",
        "rang": rang,
        "niveau_manoir": niveau_manoir,
        "priorite": priorite,
        "raccourci": str(RACCOURCIS_DIR / f"BlueStacks_{manoir_id}.lnk"),
    }


def charger_config_depuis_fichier(filepath):
    """Charge une configuration depuis un fichier JSON

    Args:
        filepath: Chemin vers le fichier JSON

    Returns:
        bool: True si chargé avec succès
    """
    import json

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            config = json.load(f)

        global MANOIRS_CONFIG
        MANOIRS_CONFIG.update(config)

        return True
    except Exception as e:
        print(f"Erreur chargement config: {e}")
        return False


def sauvegarder_config(filepath):
    """Sauvegarde la configuration dans un fichier JSON

    Args:
        filepath: Chemin vers le fichier JSON

    Returns:
        bool: True si sauvegardé avec succès
    """
    import json

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(MANOIRS_CONFIG, f, indent=2, ensure_ascii=False)

        return True
    except Exception as e:
        print(f"Erreur sauvegarde config: {e}")
        return False
