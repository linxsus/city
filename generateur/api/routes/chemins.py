"""Routes API pour la gestion des chemins."""

from fastapi import APIRouter, HTTPException

from ...generators.chemin_generator import CheminGenerator
from ...models.schemas import APIResponse, CheminCreate
from ...services.chemin_service import get_chemin_service

router = APIRouter(prefix="/chemins", tags=["Chemins"])


@router.get("/states")
async def get_available_states() -> APIResponse:
    """Récupère la liste des états disponibles pour les chemins."""
    service = get_chemin_service()
    states = service.get_existing_states()

    return APIResponse(
        success=True,
        data={"states": states},
    )


@router.post("/suggest-exits")
async def suggest_exit_states(etat_sortie: str) -> APIResponse:
    """Suggère des états de sortie possibles (popups, erreurs)."""
    service = get_chemin_service()
    suggestions = service.suggest_exit_states(etat_sortie)

    return APIResponse(
        success=True,
        data={"suggestions": suggestions},
    )


@router.post("/validate")
async def validate_chemin(data: CheminCreate) -> APIResponse:
    """Valide les données d'un chemin sans le créer."""
    service = get_chemin_service()
    errors = service.validate_chemin(data)

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


@router.post("/preview")
async def preview_chemin(data: CheminCreate) -> APIResponse:
    """Prévisualise le code généré pour un chemin."""
    service = get_chemin_service()

    # Valider d'abord
    errors = service.validate_chemin(data)
    if errors:
        return APIResponse(
            success=False,
            error={
                "code": "VALIDATION_ERROR",
                "messages": errors,
            },
        )

    # Créer le chemin
    chemin = service.create_chemin(data)

    # Générer la prévisualisation
    generator = CheminGenerator()
    preview = generator.preview(chemin)

    return APIResponse(
        success=True,
        data=preview,
    )


@router.post("/create")
async def create_chemin(data: CheminCreate) -> APIResponse:
    """Crée un nouveau chemin et génère le code."""
    service = get_chemin_service()

    # Valider
    errors = service.validate_chemin(data)
    if errors:
        return APIResponse(
            success=False,
            error={
                "code": "VALIDATION_ERROR",
                "messages": errors,
            },
        )

    try:
        # Créer le chemin
        chemin = service.create_chemin(data)

        # Générer et sauvegarder le code
        generator = CheminGenerator()
        filepath = generator.save(chemin)

        return APIResponse(
            success=True,
            data={
                "nom": chemin.nom,
                "nom_classe": chemin.nom_classe,
                "fichier_genere": str(filepath),
                "etat_initial": chemin.etat_initial,
                "etat_sortie": chemin.etat_sortie,
            },
            message=f"Chemin '{chemin.nom}' créé avec succès",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
