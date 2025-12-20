# -*- coding: utf-8 -*-
"""Package manoirs - Gestion des manoirs d'automatisation"""

from manoirs.manoir_base import ManoirBase
from manoirs.config_manoirs import (
    MANOIRS_CONFIG,
    LARGEUR_DEFAUT,
    HAUTEUR_DEFAUT,
    get_config,
    get_all_manoir_ids,
    get_farm_ids,
    get_principal_id,
    ajouter_farm,
)
