"""Routes de l'API."""

from .etats import router as etats_router
from .chemins import router as chemins_router
from .images import router as images_router
from .ia import router as ia_router
from .erreur_routes import router as erreurs_router
from .database_routes import router as database_router
from .sync_routes import router as sync_router

__all__ = [
    "etats_router",
    "chemins_router",
    "images_router",
    "ia_router",
    "erreurs_router",
    "database_router",
    "sync_router",
]
