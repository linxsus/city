# -*- coding: utf-8 -*-
"""Package utilitaires"""
from utils.config import *
from utils.logger import setup_logging, get_manoir_logger, get_module_logger
from utils.coordinates import (
    relative_to_absolute,
    absolute_to_relative,
    get_window_size,
    get_window_center,
    is_point_in_window,
    region_to_absolute,
    clamp_to_window,
)
