"""Routes API pour la gestion des états."""

from fastapi import APIRouter, HTTPException

from ...generators.etat_generator import EtatGenerator
from ...models.schemas import APIResponse, EtatCreate, EtatSchema
from ...services.etat_service import get_etat_service

router = APIRouter(prefix="/etats", tags=["États"])


@router.get("/groups")
async def get_groups() -> APIResponse:
    """Récupère la liste des groupes existants."""
    service = get_etat_service()
    groups = service.get_existing_groups()

    return APIResponse(
        success=True,
        data={"groups": groups},
    )


@router.get("/existing")
async def get_existing_states() -> APIResponse:
    """Récupère la liste des états existants."""
    service = get_etat_service()
    states = service.get_existing_states()

    return APIResponse(
        success=True,
        data={"states": states},
    )


@router.post("/validate")
async def validate_etat(data: EtatCreate) -> APIResponse:
    """Valide les données d'un état sans le créer."""
    service = get_etat_service()
    errors = service.validate_etat(data)

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
async def preview_etat(data: EtatCreate) -> APIResponse:
    """Prévisualise le code généré pour un état."""
    service = get_etat_service()

    # Valider d'abord
    errors = service.validate_etat(data)
    if errors:
        return APIResponse(
            success=False,
            error={
                "code": "VALIDATION_ERROR",
                "messages": errors,
            },
        )

    # Créer l'état (sans sauvegarder le template)
    etat = service.create_etat(data, save_template=False)

    # Générer la prévisualisation
    generator = EtatGenerator()
    preview = generator.preview(etat)

    return APIResponse(
        success=True,
        data=preview,
    )


@router.post("/create")
async def create_etat(data: EtatCreate) -> APIResponse:
    """Crée un nouvel état et génère le code."""
    service = get_etat_service()

    # Valider
    errors = service.validate_etat(data)
    if errors:
        return APIResponse(
            success=False,
            error={
                "code": "VALIDATION_ERROR",
                "messages": errors,
            },
        )

    try:
        # Créer l'état
        etat = service.create_etat(data, save_template=True)

        # Générer et sauvegarder le code
        generator = EtatGenerator()
        filepath = generator.save(etat)

        return APIResponse(
            success=True,
            data={
                "nom": etat.nom,
                "nom_classe": etat.nom_classe,
                "fichier_genere": str(filepath),
                "template_path": etat.template_path,
            },
            message=f"État '{etat.nom}' créé avec succès",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check-duplicate")
async def check_duplicate_template(
    image_source: str,
    region_x: int,
    region_y: int,
    region_width: int,
    region_height: int,
) -> APIResponse:
    """Vérifie si un template similaire existe déjà."""
    from ...models.schemas import RegionSchema

    service = get_etat_service()
    region = RegionSchema(
        x=region_x,
        y=region_y,
        width=region_width,
        height=region_height,
    )

    duplicates = service.check_duplicate_template(image_source, region)

    return APIResponse(
        success=True,
        data={
            "has_duplicates": len(duplicates) > 0,
            "duplicates": duplicates,
        },
    )
