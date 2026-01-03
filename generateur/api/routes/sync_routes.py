"""Routes API pour la synchronisation bidirectionnelle."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ...models.schemas import APIResponse
from ...services.sync_service import get_sync_service


router = APIRouter(prefix="/sync", tags=["Synchronisation"])


# === Schemas ===

class AcceptChangeRequest(BaseModel):
    """Données pour accepter un changement."""
    file_path: str = Field(..., description="Chemin du fichier")
    element_name: str = Field(..., description="Nom de l'élément")


# === Routes ===

@router.get("/status")
async def get_sync_status() -> APIResponse:
    """
    Retourne le statut de synchronisation global.

    Détecte les fichiers modifiés, nouveaux ou supprimés depuis la dernière sync.
    """
    service = get_sync_service()
    status = service.get_sync_status()

    return APIResponse(
        success=True,
        data=status,
    )


@router.get("/changes")
async def list_changes(element_type: str | None = None) -> APIResponse:
    """
    Liste les changements détectés.

    Args:
        element_type: Filtrer par type (etat, chemin, action)
    """
    service = get_sync_service()
    status = service.get_sync_status()

    changes = status["changes"]
    if element_type:
        changes = [c for c in changes if c["element_type"] == element_type]

    return APIResponse(
        success=True,
        data={
            "count": len(changes),
            "changes": changes,
        },
    )


@router.post("/sync-all")
async def sync_all() -> APIResponse:
    """
    Synchronise tous les éléments du code vers la base de données.

    Met à jour les versions stockées pour correspondre au code actuel.
    """
    service = get_sync_service()
    result = service.sync_all()

    return APIResponse(
        success=result["success"],
        data={
            "synced_count": result["synced_count"],
            "synced": result["synced"],
            "errors": result["errors"],
        },
        message=f"{result['synced_count']} éléments synchronisés",
    )


@router.post("/sync/{element_name}")
async def sync_element(element_name: str) -> APIResponse:
    """
    Synchronise un élément spécifique.

    Args:
        element_name: Nom de l'élément à synchroniser
    """
    service = get_sync_service()
    result = service.sync_from_code(element_name=element_name)

    if result["synced_count"] == 0 and len(result["errors"]) == 0:
        return APIResponse(
            success=False,
            error={
                "code": "NOT_FOUND",
                "message": f"Élément '{element_name}' non trouvé",
            },
        )

    return APIResponse(
        success=result["success"],
        data=result,
        message=f"Élément '{element_name}' synchronisé" if result["success"] else "Erreur de synchronisation",
    )


@router.post("/accept")
async def accept_change(data: AcceptChangeRequest) -> APIResponse:
    """
    Accepte un changement détecté et met à jour la version stockée.

    Utilisé pour confirmer qu'un changement manuel dans le code est intentionnel.
    """
    service = get_sync_service()
    result = service.accept_change(data.file_path, data.element_name)

    if not result["success"]:
        return APIResponse(
            success=False,
            error={
                "code": "ACCEPT_FAILED",
                "message": result.get("error", "Erreur inconnue"),
            },
        )

    return APIResponse(
        success=True,
        data=result,
        message=result["message"],
    )


@router.post("/ignore")
async def ignore_change(data: AcceptChangeRequest) -> APIResponse:
    """
    Ignore un changement et supprime le tracking pour cet élément.

    Utilisé pour arrêter de suivre un fichier/élément.
    """
    service = get_sync_service()
    result = service.ignore_change(data.file_path, data.element_name)

    return APIResponse(
        success=True,
        data=result,
        message=result["message"],
    )


@router.get("/history/{element_name}")
async def get_element_history(element_name: str) -> APIResponse:
    """
    Récupère l'historique de synchronisation d'un élément.

    Args:
        element_name: Nom de l'élément
    """
    service = get_sync_service()
    history = service.get_element_history(element_name)

    return APIResponse(
        success=True,
        data=history,
    )


@router.get("/tracked")
async def list_tracked_elements() -> APIResponse:
    """Liste tous les éléments actuellement suivis."""
    from ...services.database_service import get_database_service

    db = get_database_service()
    versions = db.get_all_file_versions()

    # Grouper par type
    by_type = {}
    for v in versions:
        elem_type = v["element_type"]
        if elem_type not in by_type:
            by_type[elem_type] = []
        by_type[elem_type].append({
            "name": v["element_name"],
            "file": v["file_path"],
            "version": v["version"],
            "last_sync": v["last_sync_at"],
        })

    return APIResponse(
        success=True,
        data={
            "total": len(versions),
            "by_type": by_type,
        },
    )
