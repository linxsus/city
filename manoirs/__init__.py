"""Package manoirs - Gestion des manoirs d'automatisation"""

__all__ = [
    "ManoirBase",
    "MANOIRS_CONFIG",
    "LARGEUR_DEFAUT",
    "HAUTEUR_DEFAUT",
    "get_config",
    "get_all_manoir_ids",
    "get_farm_ids",
    "get_principal_id",
    "ajouter_farm",
]

from manoirs.config_manoirs import (
    HAUTEUR_DEFAUT,
    LARGEUR_DEFAUT,
    MANOIRS_CONFIG,
    ajouter_farm,
    get_all_manoir_ids,
    get_config,
    get_farm_ids,
    get_principal_id,
)
from manoirs.manoir_base import ManoirBase
