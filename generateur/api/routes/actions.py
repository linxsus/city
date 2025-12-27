"""Routes API pour la gestion des actions."""

from fastapi import APIRouter, HTTPException

from ...models.schemas import APIResponse
from ...models.schemas_action_longue import ActionLongueCreate
from ...services.action_longue_service import get_action_longue_service

router = APIRouter(prefix="/actions", tags=["Actions"])


@router.get("/longue/list")
async def list_actions_longues() -> APIResponse:
    """Liste toutes les ActionLongue existantes."""
    service = get_action_longue_service()
    actions = service.list_actions()

    return APIResponse(
        success=True,
        data={"actions": actions},
    )


@router.get("/longue/workspace/{nom}")
async def get_workspace(nom: str) -> APIResponse:
    """Récupère le workspace Blockly d'une ActionLongue."""
    service = get_action_longue_service()
    workspace = service.get_workspace(nom)

    if workspace is None:
        return APIResponse(
            success=False,
            error={
                "code": "NOT_FOUND",
                "message": f"Workspace non trouvé pour l'action '{nom}'",
            },
        )

    return APIResponse(
        success=True,
        data={"workspace": workspace},
    )


@router.post("/longue/validate")
async def validate_action_longue(data: ActionLongueCreate) -> APIResponse:
    """Valide les données d'une ActionLongue sans la créer."""
    service = get_action_longue_service()
    errors = service.validate_action_longue(data)

    if errors:
        return APIResponse(
            success=False,
            error={
                "code": "VALIDATION_ERROR",
                "messages": errors,
            },
        )

    return APIResponse(
        success=True,
        message="Données valides",
    )


@router.post("/longue/create")
async def create_action_longue(data: ActionLongueCreate) -> APIResponse:
    """Crée une nouvelle ActionLongue et génère le code."""
    service = get_action_longue_service()

    # Valider
    errors = service.validate_action_longue(data)
    if errors:
        return APIResponse(
            success=False,
            error={
                "code": "VALIDATION_ERROR",
                "messages": errors,
            },
        )

    try:
        # Créer l'action
        action = service.create_action_longue(data)

        return APIResponse(
            success=True,
            data={
                "nom": action.nom,
                "fichier_genere": action.fichier_genere,
                "etat_requis": action.etat_requis,
            },
            message=f"ActionLongue '{action.nom}' créée avec succès",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
