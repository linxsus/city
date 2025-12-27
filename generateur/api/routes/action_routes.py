"""Routes API pour les actions."""

from fastapi import APIRouter

from ...models.schemas import ActionCreate, ActionLongueCreate, APIResponse
from ...services.action_service import get_action_longue_service, get_action_service
from ...services.import_service import get_import_service

router = APIRouter(prefix="/actions", tags=["Actions"])


@router.get("/available")
async def get_available_actions() -> APIResponse:
    """Liste toutes les actions disponibles (simples et longues)."""
    try:
        service = get_import_service()
        actions = service.get_all_actions()

        # Séparer les actions simples et longues
        simples = []
        longues = []

        for action in actions:
            action_dict = action.to_dict()
            if action.action_type == "simple":
                simples.append(action_dict)
            else:
                longues.append(action_dict)

        # Ajouter les actions de base du framework
        base_actions = [
            {"nom": "ActionBouton", "nom_classe": "ActionBouton", "description": "Clic sur une image/template", "action_type": "base"},
            {"nom": "ActionAttendre", "nom_classe": "ActionAttendre", "description": "Attente non-bloquante", "action_type": "base"},
            {"nom": "ActionTexte", "nom_classe": "ActionTexte", "description": "Clic sur un texte détecté par OCR", "action_type": "base"},
            {"nom": "ActionLog", "nom_classe": "ActionLog", "description": "Log un message", "action_type": "base"},
        ]

        return APIResponse(
            success=True,
            data={
                "base": base_actions,
                "simples": simples,
                "longues": longues,
            },
        )
    except Exception as e:
        return APIResponse(
            success=False,
            error={
                "code": "LIST_ERROR",
                "message": str(e),
            },
        )


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
