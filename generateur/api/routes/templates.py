"""Routes API pour la gestion des templates multi-variantes."""

from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from ...models.schemas import (
    APIResponse,
    RegionSchema,
    TemplateConfigCreate,
    TemplateListItem,
    VariantCreate,
)
from ...services.template_service import get_template_service
from ...services.image_service import get_image_service

router = APIRouter(prefix="/templates", tags=["Templates"])


# =====================================================
# LISTE ET CONSULTATION
# =====================================================


@router.get("/list")
async def list_templates(category: str | None = None) -> APIResponse:
    """Liste tous les templates disponibles.

    Args:
        category: Filtrer par catégorie (optionnel)
    """
    service = get_template_service()
    templates = service.list_templates(category)

    return APIResponse(
        success=True,
        data={
            "templates": [t.model_dump() for t in templates],
            "count": len(templates),
        },
    )


@router.get("/categories")
async def list_categories() -> APIResponse:
    """Liste toutes les catégories de templates."""
    service = get_template_service()
    categories = service.list_categories()

    return APIResponse(
        success=True,
        data={"categories": categories},
    )


@router.get("/groups")
async def list_groups() -> APIResponse:
    """Liste tous les groupes utilisés dans les templates."""
    service = get_template_service()
    groups = service.list_groups()

    return APIResponse(
        success=True,
        data={"groups": groups},
    )


@router.get("/{template_name}")
async def get_template(template_name: str) -> APIResponse:
    """Récupère la configuration d'un template."""
    service = get_template_service()
    config = service.get_template(template_name)

    if not config:
        return APIResponse(
            success=False,
            error={
                "code": "NOT_FOUND",
                "message": f"Template '{template_name}' non trouvé",
            },
        )

    return APIResponse(
        success=True,
        data=config,
    )


# =====================================================
# CRÉATION ET MODIFICATION
# =====================================================


@router.post("/create")
async def create_template(data: TemplateConfigCreate) -> APIResponse:
    """Crée un nouveau template.

    Args:
        data: Configuration du template
    """
    service = get_template_service()

    try:
        template_dir = service.create_template(data)

        return APIResponse(
            success=True,
            data={
                "name": data.name,
                "category": data.category,
                "path": str(template_dir),
            },
            message=f"Template '{data.name}' créé avec succès",
        )

    except ValueError as e:
        return APIResponse(
            success=False,
            error={
                "code": "ALREADY_EXISTS",
                "message": str(e),
            },
        )


class TemplateUpdateData(BaseModel):
    """Données pour mettre à jour un template."""
    description: str | None = None
    group_configs: dict | None = None


@router.put("/{template_name}")
async def update_template(template_name: str, data: TemplateUpdateData) -> APIResponse:
    """Met à jour la configuration d'un template."""
    service = get_template_service()

    if not service.update_template(template_name, data.model_dump(exclude_none=True)):
        return APIResponse(
            success=False,
            error={
                "code": "NOT_FOUND",
                "message": f"Template '{template_name}' non trouvé",
            },
        )

    return APIResponse(
        success=True,
        message=f"Template '{template_name}' mis à jour",
    )


@router.delete("/{template_name}")
async def delete_template(template_name: str) -> APIResponse:
    """Supprime un template et toutes ses variantes."""
    service = get_template_service()

    if not service.delete_template(template_name):
        return APIResponse(
            success=False,
            error={
                "code": "NOT_FOUND",
                "message": f"Template '{template_name}' non trouvé",
            },
        )

    return APIResponse(
        success=True,
        message=f"Template '{template_name}' supprimé",
    )


# =====================================================
# VARIANTES
# =====================================================


@router.post("/{template_name}/variants")
async def add_variant(
    template_name: str,
    group: str,
    variant_name: str,
    image_path: str,
    x: int | None = None,
    y: int | None = None,
    width: int | None = None,
    height: int | None = None,
    threshold: float | None = None,
    force: bool = False,
) -> APIResponse:
    """Ajoute une variante à un template.

    Args:
        template_name: Nom du template
        group: Groupe de la variante
        variant_name: Nom du fichier
        image_path: Chemin de l'image source
        x, y, width, height: Région à extraire (optionnel)
        threshold: Seuil spécifique (optionnel)
        force: Forcer l'ajout même si duplicata détecté
    """
    service = get_template_service()

    # Construire la région si spécifiée
    region = None
    if all(v is not None for v in [x, y, width, height]):
        region = RegionSchema(x=x, y=y, width=width, height=height)

    result = service.add_variant(
        template_name=template_name,
        group=group,
        variant_name=variant_name,
        image_path=image_path,
        region=region,
        threshold=threshold,
        force=force,
    )

    if not result.get("success"):
        return APIResponse(
            success=False,
            error={
                "code": "DUPLICATE" if result.get("requires_force") else "ERROR",
                "message": result.get("error", "Erreur inconnue"),
            },
            data={
                "duplicates": result.get("duplicates", []),
                "similar": result.get("similar", []),
                "requires_force": result.get("requires_force", False),
            },
        )

    return APIResponse(
        success=True,
        data={
            "variant": variant_name,
            "group": group,
            "path": result.get("path"),
            "hash": result.get("hash"),
        },
        message=result.get("message", "Variante ajoutée avec succès"),
    )


@router.post("/{template_name}/variants/upload")
async def upload_variant(
    template_name: str,
    group: str,
    variant_name: str,
    file: UploadFile = File(...),
    threshold: float | None = None,
    force: bool = False,
) -> APIResponse:
    """Upload une image comme variante.

    Args:
        template_name: Nom du template
        group: Groupe de la variante
        variant_name: Nom du fichier
        file: Image à uploader
        threshold: Seuil spécifique (optionnel)
        force: Forcer l'ajout même si duplicata détecté
    """
    # Vérifier le type de fichier
    if not file.content_type or not file.content_type.startswith("image/"):
        return APIResponse(
            success=False,
            error={
                "code": "INVALID_FILE_TYPE",
                "message": "Le fichier doit être une image (PNG, JPG)",
            },
        )

    # Sauvegarder temporairement l'image
    image_service = get_image_service()
    content = await file.read()
    temp_path = image_service.save_upload(content, file.filename or "upload.png")

    # Ajouter la variante
    template_service = get_template_service()

    result = template_service.add_variant(
        template_name=template_name,
        group=group,
        variant_name=variant_name,
        image_path=str(temp_path),
        threshold=threshold,
        force=force,
    )

    # Supprimer le fichier temporaire
    image_service.cleanup_upload(str(temp_path))

    if not result.get("success"):
        return APIResponse(
            success=False,
            error={
                "code": "DUPLICATE" if result.get("requires_force") else "ERROR",
                "message": result.get("error", "Erreur inconnue"),
            },
            data={
                "duplicates": result.get("duplicates", []),
                "similar": result.get("similar", []),
                "requires_force": result.get("requires_force", False),
            },
        )

    return APIResponse(
        success=True,
        data={
            "variant": variant_name,
            "group": group,
            "path": result.get("path"),
            "hash": result.get("hash"),
        },
        message=result.get("message", "Variante uploadée avec succès"),
    )


@router.delete("/{template_name}/variants/{group}/{variant_name}")
async def delete_variant(
    template_name: str,
    group: str,
    variant_name: str,
) -> APIResponse:
    """Supprime une variante d'un template."""
    service = get_template_service()

    if not service.delete_variant(template_name, group, variant_name):
        return APIResponse(
            success=False,
            error={
                "code": "NOT_FOUND",
                "message": "Template, groupe ou variante non trouvé",
            },
        )

    return APIResponse(
        success=True,
        message=f"Variante '{variant_name}' supprimée",
    )


@router.get("/{template_name}/variants/{variant_name}")
async def serve_variant(template_name: str, variant_name: str):
    """Sert une image de variante."""
    service = get_template_service()
    variant_path = service.get_variant_path(template_name, variant_name)

    if not variant_path:
        raise HTTPException(status_code=404, detail="Variante non trouvée")

    return FileResponse(variant_path)


# =====================================================
# TEST DE TEMPLATES
# =====================================================


@router.post("/{template_name}/test")
async def test_template(
    template_name: str,
    image_path: str,
    groups: list[str] | None = None,
) -> APIResponse:
    """Teste un template sur une image.

    Args:
        template_name: Nom du template
        image_path: Chemin de l'image à tester
        groups: Groupes à tester (tous si non spécifié)
    """
    from PIL import Image
    from vision.image_matcher import get_image_matcher

    template_service = get_template_service()
    config = template_service.get_template(template_name)

    if not config:
        return APIResponse(
            success=False,
            error={
                "code": "NOT_FOUND",
                "message": f"Template '{template_name}' non trouvé",
            },
        )

    # Charger l'image à tester
    try:
        test_image = Image.open(image_path)
    except Exception as e:
        return APIResponse(
            success=False,
            error={
                "code": "IMAGE_ERROR",
                "message": f"Erreur de chargement de l'image: {e}",
            },
        )

    matcher = get_image_matcher()
    base_path = Path(config["base_path"])
    results = []

    # Tester chaque groupe demandé
    groups_to_test = groups or list(config.get("group_configs", {}).keys())

    for group in groups_to_test:
        group_config = config.get("group_configs", {}).get(group)
        if not group_config:
            continue

        threshold = group_config.get("threshold", 0.8)

        for variant in group_config.get("variants", []):
            variant_path = base_path / variant

            if not variant_path.exists():
                results.append({
                    "variant": variant,
                    "group": group,
                    "found": False,
                    "error": "Fichier non trouvé",
                })
                continue

            result = matcher.find_template(test_image, str(variant_path), threshold)

            if result:
                x, y, confidence = result
                results.append({
                    "variant": variant,
                    "group": group,
                    "found": True,
                    "position": (x, y),
                    "confidence": round(confidence, 3),
                    "threshold": threshold,
                })
            else:
                results.append({
                    "variant": variant,
                    "group": group,
                    "found": False,
                    "threshold": threshold,
                })

    # Trier : trouvés d'abord, puis par confiance décroissante
    results.sort(key=lambda r: (not r.get("found", False), -r.get("confidence", 0)))

    return APIResponse(
        success=True,
        data={
            "template": template_name,
            "results": results,
            "found_count": sum(1 for r in results if r.get("found")),
            "total_count": len(results),
        },
    )


# =====================================================
# DÉTECTION DE DUPLICATAS ET INDEXATION (Phase 3)
# =====================================================


@router.post("/check-duplicate")
async def check_duplicate(
    image_path: str,
    x: int | None = None,
    y: int | None = None,
    width: int | None = None,
    height: int | None = None,
    exact_threshold: float = 0.95,
    similar_threshold: float = 0.85,
) -> APIResponse:
    """Vérifie si une image est un duplicata d'un template existant.

    Args:
        image_path: Chemin de l'image à vérifier
        x, y, width, height: Région à extraire (optionnel)
        exact_threshold: Seuil pour duplicata exact (défaut: 0.95)
        similar_threshold: Seuil pour image similaire (défaut: 0.85)
    """
    service = get_template_service()

    # Construire la région si spécifiée
    region = None
    if all(v is not None for v in [x, y, width, height]):
        region = RegionSchema(x=x, y=y, width=width, height=height)

    result = service.check_duplicate(
        image_path=image_path,
        region=region,
        exact_threshold=exact_threshold,
        similar_threshold=similar_threshold,
    )

    return APIResponse(
        success=True,
        data=result,
    )


@router.post("/index-all")
async def index_all_templates() -> APIResponse:
    """Indexe tous les templates existants dans la base de données.

    Calcule le hash perceptuel (dHash) de chaque template et le stocke
    pour permettre la détection rapide de duplicatas.
    """
    service = get_template_service()
    result = service.index_all_templates()

    return APIResponse(
        success=True,
        data=result,
        message=result.get("message"),
    )
