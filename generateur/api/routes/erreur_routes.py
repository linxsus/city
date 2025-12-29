"""Routes API pour la gestion des erreurs."""

from fastapi import APIRouter

from ...models.schemas import APIResponse, ErreurCreate
from ...services.erreur_service import get_erreur_service

router = APIRouter(prefix="/erreurs", tags=["Erreurs"])


@router.get("/")
async def get_all_erreurs() -> APIResponse:
    """Récupère toutes les erreurs disponibles."""
    service = get_erreur_service()
    erreurs = service.get_all_erreurs()

    return APIResponse(
        success=True,
        data={
            "erreurs": [e.model_dump() for e in erreurs],
            "count": len(erreurs),
        },
    )


@router.get("/categories")
async def get_categories() -> APIResponse:
    """Récupère la liste des catégories d'erreurs."""
    service = get_erreur_service()

    return APIResponse(
        success=True,
        data={"categories": service.get_categories()},
    )


@router.get("/by-category/{categorie}")
async def get_erreurs_by_category(categorie: str) -> APIResponse:
    """Récupère les erreurs d'une catégorie spécifique."""
    service = get_erreur_service()
    erreurs = service.get_erreurs_by_category(categorie)

    return APIResponse(
        success=True,
        data={
            "erreurs": [e.model_dump() for e in erreurs],
            "categorie": categorie,
            "count": len(erreurs),
        },
    )


@router.get("/defaults/verif-apres")
async def get_erreurs_verif_apres_defaults() -> APIResponse:
    """Récupère les erreurs par défaut à vérifier après chaque action."""
    service = get_erreur_service()
    defaults = service.get_erreurs_verif_apres_defaults()

    return APIResponse(
        success=True,
        data={"erreurs": defaults},
    )


@router.get("/defaults/si-echec")
async def get_erreurs_si_echec_defaults() -> APIResponse:
    """Récupère les erreurs par défaut à vérifier si échec."""
    service = get_erreur_service()
    defaults = service.get_erreurs_si_echec_defaults()

    return APIResponse(
        success=True,
        data={"erreurs": defaults},
    )


@router.get("/{nom}")
async def get_erreur_by_nom(nom: str) -> APIResponse:
    """Récupère une erreur par son nom."""
    service = get_erreur_service()
    erreur = service.get_erreur_by_nom(nom)

    if erreur is None:
        return APIResponse(
            success=False,
            error={
                "code": "NOT_FOUND",
                "message": f"Erreur '{nom}' non trouvée",
            },
        )

    return APIResponse(
        success=True,
        data={"erreur": erreur.model_dump()},
    )


@router.post("/refresh")
async def refresh_erreurs() -> APIResponse:
    """Recharge les erreurs depuis le fichier source."""
    service = get_erreur_service()
    service.invalidate_cache()
    erreurs = service.get_all_erreurs()

    return APIResponse(
        success=True,
        data={"count": len(erreurs)},
        message=f"{len(erreurs)} erreurs rechargées",
    )
