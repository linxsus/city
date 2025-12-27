"""Routes API pour les actions."""

from fastapi import APIRouter

from ...models.schemas import ActionCreate, ActionLongueCreate, APIResponse
from ...services.action_service import get_action_longue_service, get_action_service

router = APIRouter(prefix="/actions", tags=["Actions"])


@router.post("/simple/preview")
async def preview_action(data: ActionCreate) -> APIResponse:
    """Prévisualise le code d'une action simple."""
    try:
        service = get_action_service()
        result = service.preview(data)

        return APIResponse(
            success=True,
            data=result,
        )
    except Exception as e:
        return APIResponse(
            success=False,
            error={
                "code": "PREVIEW_ERROR",
                "message": str(e),
            },
        )


@router.post("/simple/generate")
async def generate_action(data: ActionCreate) -> APIResponse:
    """Génère et sauvegarde une action simple."""
    try:
        service = get_action_service()
        result = service.save(data)

        return APIResponse(
            success=True,
            data=result,
            message=f"Action {result['class_name']} générée avec succès",
        )
    except Exception as e:
        return APIResponse(
            success=False,
            error={
                "code": "GENERATION_ERROR",
                "message": str(e),
            },
        )


@router.post("/longue/preview")
async def preview_action_longue(data: ActionLongueCreate) -> APIResponse:
    """Prévisualise le code d'une action longue."""
    try:
        service = get_action_longue_service()
        result = service.preview(data)

        return APIResponse(
            success=True,
            data=result,
        )
    except Exception as e:
        return APIResponse(
            success=False,
            error={
                "code": "PREVIEW_ERROR",
                "message": str(e),
            },
        )


@router.post("/longue/generate")
async def generate_action_longue(data: ActionLongueCreate) -> APIResponse:
    """Génère et sauvegarde une action longue."""
    try:
        service = get_action_longue_service()
        result = service.save(data)

        return APIResponse(
            success=True,
            data=result,
            message=f"ActionLongue {result['class_name']} générée avec succès",
        )
    except Exception as e:
        return APIResponse(
            success=False,
            error={
                "code": "GENERATION_ERROR",
                "message": str(e),
            },
        )
