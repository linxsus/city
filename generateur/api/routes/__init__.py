"""Routes de l'API."""

from .etats import router as etats_router
from .chemins import router as chemins_router
from .images import router as images_router
from .ia import router as ia_router

__all__ = [
    "etats_router",
    "chemins_router",
    "images_router",
    "ia_router",
]
