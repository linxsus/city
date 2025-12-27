"""Configuration des manoirs

Définit la configuration de chaque manoir à automatiser.
Configuration pour tests réels.
"""

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
# DIMENSIONS BLUESTACKS (pour gestion pub/bandeau)
# =====================================================
# Ces valeurs sont basées sur les mesures réelles des fenêtres BlueStacks
#
# Structure de la fenêtre BlueStacks (de gauche à droite):
# [PUB (~320px)] [ZONE DE JEU (~563px)] [BANDEAU DROIT (~32px)]
#
# Les 4 configurations correctes (hauteur fixe 1030):
# - Sans pub, sans bandeau : 563 x 1030
# - Sans pub, avec bandeau : 595 x 1030
# - Avec pub, sans bandeau : 884 x 1030
# - Avec pub, avec bandeau : 915 x 1030

# Hauteur cible pour toutes les configurations
BLUESTACKS_HAUTEUR = 1030

# Dimensions des 4 configurations possibles
BLUESTACKS_DIMENSIONS = {
    # (a_pub, a_bandeau): (largeur, hauteur)
    (False, False): (563, 1030),  # Sans pub, sans bandeau
    (False, True): (595, 1030),  # Sans pub, avec bandeau
    (True, False): (884, 1030),  # Avec pub, sans bandeau
    (True, True): (915, 1030),  # Avec pub, avec bandeau
}

# Constantes individuelles (pour compatibilité)
BLUESTACKS_LARGEUR_ZONE_JEU = 563  # Zone de jeu pure (sans bandeau)
BLUESTACKS_LARGEUR_BANDEAU = 32  # Bandeau droit avec icônes
BLUESTACKS_LARGEUR_ZONE_AVEC_BANDEAU = 595  # Zone de jeu + bandeau
BLUESTACKS_LARGEUR_PUB = 320  # Largeur approximative de la pub

# Seuils de détection
BLUESTACKS_SEUIL_PUB = 700  # Si largeur > 700, fenêtre a pub
BLUESTACKS_SEUIL_BANDEAU_SANS_PUB = 579  # Milieu entre 563 et 595
BLUESTACKS_SEUIL_BANDEAU_AVEC_PUB = 900  # Milieu entre 884 et 915

# Seuil de ratio pour détecter la présence de pub (conservé pour compatibilité)
# Sans pub: ratio ≈ 0.55-0.58 | Avec pub: ratio ≈ 0.85-0.89
BLUESTACKS_SEUIL_RATIO_PUB = 0.70


# =====================================================
# CONFIGURATION DES MANOIRS
# =====================================================

MANOIRS_CONFIG = {
    # Manoir principal - Compte principal avec BlueStacks (DÉSACTIVÉ)
    # "principal": {
    #     "nom": "Manoir Principal",
    #     "titre_bluestacks": "principal",
    #     "type": "principal",
    #     "priorite": 50,
    #     "largeur": 600,
    #     "hauteur": 1040,
    #     "position_x": 0,
    #     "position_y": 0,
    #     "commande_lancement": [
    #         BLUESTACKS_PLAYER,
    #         "--instance",
    #         "Nougat32_1",
    #         "--cmd",
    #         "launchAppWithBsx",
    #         "--package",
    #         "com.yottagames.mafiawar",
    #         "--source",
    #         "desktop_shortcut",
    #     ],
    #     "temps_initialisation": 300,
    # },

    # Exemple Manoir Scrcpy - Appareil Android via USB
    "android": {
        "nom": "Android Principal",
        "type": "scrcpy",
        "priorite": 50,
        # Dimensions de référence (scrcpy avec -m 1024)
        "largeur": 1024,
        "hauteur": 576,
        # Options scrcpy
        "scrcpy_max_size": 1024,
        # Serial appareil (None pour auto-détection)
        "device_serial": None,
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
    return [mid for mid, config in MANOIRS_CONFIG.items() if config.get("type") == type_manoir]


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
        with open(filepath, encoding="utf-8") as f:
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
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(MANOIRS_CONFIG, f, indent=2, ensure_ascii=False)

        return True
    except Exception as e:
        print(f"Erreur sauvegarde config: {e}")
        return False
