"""Routes API pour les fonctionnalités IA (Claude)."""

from fastapi import APIRouter

from ...config import get_existing_groups, is_claude_available
from ...models.schemas import APIResponse
from ...services.claude_service import get_claude_service

router = APIRouter(prefix="/ia", tags=["IA Claude"])


@router.get("/status")
async def get_ia_status() -> APIResponse:
    """Vérifie si l'API Claude est disponible."""
    available = is_claude_available()

    return APIResponse(
        success=True,
        data={
            "available": available,
            "message": (
                "API Claude configurée et prête"
                if available
                else "API Claude non configurée. Ajoutez ANTHROPIC_API_KEY dans .env"
            ),
        },
    )


@router.post("/analyze")
async def analyze_image(
    image_path: str,
    contexte: str | None = None,
) -> APIResponse:
    """
    Analyse une image avec Claude pour suggérer les zones caractéristiques.

    Retourne:
    - Régions suggérées pour la détection
    - Textes détectés
    - Groupe suggéré
    - Priorité suggérée
    """
    service = get_claude_service()

    if not service.is_available():
        return APIResponse(
            success=False,
            error={
                "code": "IA_NOT_AVAILABLE",
                "message": "API Claude non configurée. Mode manuel uniquement.",
            },
        )

    try:
        groupes_existants = get_existing_groups()
        suggestion = await service.analyser_image(
            image_path=image_path,
            contexte=contexte,
            groupes_existants=groupes_existants,
        )

        return APIResponse(
            success=True,
            data={
                "regions": suggestion.regions,
                "textes": suggestion.textes,
                "groupe_suggere": suggestion.groupe_suggere,
                "priorite_suggeree": suggestion.priorite_suggeree,
                "explication": suggestion.explication,
            },
        )

    except Exception as e:
        return APIResponse(
            success=False,
            error={
                "code": "IA_ERROR",
                "message": str(e),
            },
        )


@router.post("/detect-buttons")
async def detect_buttons(image_path: str) -> APIResponse:
    """
    Détecte les zones cliquables dans une image.

    Retourne une liste de boutons avec leurs coordonnées et descriptions.
    """
    service = get_claude_service()

    if not service.is_available():
        return APIResponse(
            success=False,
            error={
                "code": "IA_NOT_AVAILABLE",
                "message": "API Claude non configurée. Mode manuel uniquement.",
            },
        )

    try:
        boutons = await service.detecter_boutons(image_path)

        return APIResponse(
            success=True,
            data={
                "boutons": boutons,
                "count": len(boutons),
            },
        )

    except Exception as e:
        return APIResponse(
            success=False,
            error={
                "code": "IA_ERROR",
                "message": str(e),
            },
        )
