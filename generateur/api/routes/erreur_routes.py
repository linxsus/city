"""Routes API pour la gestion des erreurs."""

from fastapi import APIRouter
from pydantic import BaseModel

from ...generators.erreur_generator import ErreurGenerator
from ...models.schemas import APIResponse, ErreurCreate
from ...services.claude_service import get_claude_service
from ...services.erreur_service import get_erreur_service

router = APIRouter(prefix="/erreurs", tags=["Erreurs"])


class SuggestionRequest(BaseModel):
    """Requête pour suggérer des erreurs."""
    action_description: str


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


@router.post("/preview")
async def preview_erreur(data: ErreurCreate) -> APIResponse:
    """Prévisualise le code généré pour une erreur."""
    generator = ErreurGenerator()
    preview = generator.preview(data)

    return APIResponse(
        success=True,
        data=preview,
    )


@router.post("/create")
async def create_erreur(data: ErreurCreate) -> APIResponse:
    """Crée une nouvelle erreur et l'ajoute à liste_erreurs.py."""
    service = get_erreur_service()

    # Vérifier si l'erreur existe déjà
    existing = service.get_erreur_by_nom(data.nom)
    if existing:
        return APIResponse(
            success=False,
            error={
                "code": "ALREADY_EXISTS",
                "message": f"Une erreur avec le nom '{data.nom}' existe déjà",
            },
        )

    # Générer et ajouter l'erreur
    generator = ErreurGenerator()
    success = generator.add_erreur_to_file(data)

    if success:
        # Recharger le cache
        service.invalidate_cache()

        return APIResponse(
            success=True,
            data={
                "nom": data.nom,
                "type": data.type.value,
                "categorie": data.categorie,
            },
            message=f"Erreur '{data.nom}' créée avec succès",
        )

    return APIResponse(
        success=False,
        error={
            "code": "WRITE_ERROR",
            "message": "Impossible d'écrire dans le fichier liste_erreurs.py",
        },
    )


@router.post("/suggest")
async def suggest_erreurs(request: SuggestionRequest) -> APIResponse:
    """Suggère des erreurs pertinentes pour une action via l'IA Claude."""
    erreur_service = get_erreur_service()
    claude_service = get_claude_service()

    # Vérifier si Claude est disponible
    if not claude_service.is_available():
        # Retourner les défauts si pas d'IA
        return APIResponse(
            success=True,
            data={
                "erreurs_verif_apres": erreur_service.get_erreurs_verif_apres_defaults(),
                "erreurs_si_echec": erreur_service.get_erreurs_si_echec_defaults(),
                "explication": "API Claude non disponible - valeurs par défaut utilisées",
            },
        )

    # Récupérer les erreurs disponibles
    erreurs = erreur_service.get_all_erreurs()
    erreurs_list = [e.model_dump() for e in erreurs]

    # Appeler Claude pour les suggestions
    result = await claude_service.suggerer_erreurs(
        action_description=request.action_description,
        erreurs_disponibles=erreurs_list,
    )

    return APIResponse(
        success=True,
        data=result,
    )
