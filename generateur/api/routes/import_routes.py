"""Routes API pour l'import et la visualisation des éléments existants."""

from fastapi import APIRouter

from ...models.schemas import APIResponse
from ...services.import_service import get_import_service

router = APIRouter(prefix="/import", tags=["Import"])


@router.get("/summary")
async def get_summary() -> APIResponse:
    """Récupère un résumé de tous les éléments existants."""
    service = get_import_service()
    summary = service.get_summary()

    return APIResponse(
        success=True,
        data=summary,
    )


@router.get("/etats")
async def get_all_etats() -> APIResponse:
    """Liste tous les états existants."""
    service = get_import_service()
    etats = service.get_all_etats()

    return APIResponse(
        success=True,
        data={
            "count": len(etats),
            "etats": [e.to_dict() for e in etats],
        },
    )


@router.get("/etats/{nom}")
async def get_etat_by_name(nom: str) -> APIResponse:
    """Récupère un état par son nom."""
    service = get_import_service()
    etat = service.get_etat_by_name(nom)

    if etat is None:
        return APIResponse(
            success=False,
            error={
                "code": "NOT_FOUND",
                "message": f"État '{nom}' non trouvé",
            },
        )

    return APIResponse(
        success=True,
        data=etat.to_dict(),
    )


@router.get("/chemins")
async def get_all_chemins() -> APIResponse:
    """Liste tous les chemins existants."""
    service = get_import_service()
    chemins = service.get_all_chemins()

    return APIResponse(
        success=True,
        data={
            "count": len(chemins),
            "chemins": [c.to_dict() for c in chemins],
        },
    )


@router.get("/chemins/{nom}")
async def get_chemin_by_name(nom: str) -> APIResponse:
    """Récupère un chemin par son nom."""
    service = get_import_service()
    chemin = service.get_chemin_by_name(nom)

    if chemin is None:
        return APIResponse(
            success=False,
            error={
                "code": "NOT_FOUND",
                "message": f"Chemin '{nom}' non trouvé",
            },
        )

    return APIResponse(
        success=True,
        data=chemin.to_dict(),
    )


@router.get("/templates")
async def get_all_templates() -> APIResponse:
    """Liste tous les templates existants."""
    service = get_import_service()
    templates = service.get_all_templates()

    return APIResponse(
        success=True,
        data={
            "count": len(templates),
            "templates": templates,
        },
    )


@router.get("/templates/usage")
async def get_template_usage(path: str) -> APIResponse:
    """Trouve où un template est utilisé."""
    service = get_import_service()
    usage = service.get_template_usage(path)

    return APIResponse(
        success=True,
        data=usage,
    )


@router.get("/templates/orphans")
async def get_orphan_templates() -> APIResponse:
    """Liste les templates non utilisés."""
    service = get_import_service()
    orphans = service.find_orphan_templates()

    return APIResponse(
        success=True,
        data={
            "count": len(orphans),
            "orphans": orphans,
        },
    )


@router.get("/templates/missing")
async def get_missing_templates() -> APIResponse:
    """Liste les templates référencés mais inexistants."""
    service = get_import_service()
    missing = service.find_missing_templates()

    return APIResponse(
        success=True,
        data={
            "count": len(missing),
            "missing": missing,
        },
    )


@router.get("/groupes")
async def get_all_groupes() -> APIResponse:
    """Liste tous les groupes utilisés."""
    service = get_import_service()
    summary = service.get_summary()

    return APIResponse(
        success=True,
        data={
            "groupes": summary["groupes"],
        },
    )
