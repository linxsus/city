"""Routes API pour la gestion des images."""

from pathlib import Path
from urllib.parse import unquote

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from ...config import FRAMEWORK_TEMPLATES_DIR
from ...models.schemas import APIResponse, RegionSchema
from ...services.image_service import get_image_service

router = APIRouter(prefix="/images", tags=["Images"])


@router.get("/serve")
async def serve_image(path: str):
    """Sert une image uploadée."""
    file_path = Path(path)

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image non trouvée")

    # Vérifier que le fichier est dans un dossier autorisé
    service = get_image_service()
    allowed = False

    try:
        file_path.relative_to(service.upload_dir)
        allowed = True
    except ValueError:
        pass

    if not allowed:
        try:
            file_path.relative_to(service.generated_dir)
            allowed = True
        except ValueError:
            pass

    if not allowed:
        raise HTTPException(status_code=403, detail="Accès non autorisé")

    return FileResponse(file_path)


@router.post("/upload")
async def upload_image(file: UploadFile = File(...)) -> APIResponse:
    """
    Upload une image source.

    L'image sera sauvegardée temporairement et son chemin retourné.
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

    # Vérifier la taille (max 10 Mo)
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        return APIResponse(
            success=False,
            error={
                "code": "FILE_TOO_LARGE",
                "message": "L'image ne doit pas dépasser 10 Mo",
            },
        )

    try:
        service = get_image_service()
        filepath = service.save_upload(content, file.filename or "upload.png")

        # Récupérer les infos de l'image
        info = service.get_image_info(filepath)

        return APIResponse(
            success=True,
            data={
                "path": str(filepath),
                "filename": filepath.name,
                "width": info["width"],
                "height": info["height"],
                "size_bytes": info["size_bytes"],
            },
            message="Image uploadée avec succès",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/crop")
async def crop_region(
    image_path: str,
    x: int,
    y: int,
    width: int,
    height: int,
    output_name: str | None = None,
    output_subdir: str | None = None,
) -> APIResponse:
    """Découpe une région d'une image."""
    region = RegionSchema(x=x, y=y, width=width, height=height)

    try:
        service = get_image_service()
        output_path = service.crop_region(
            image_path=image_path,
            region=region,
            output_name=output_name,
            output_subdir=output_subdir,
        )

        return APIResponse(
            success=True,
            data={
                "path": str(output_path),
                "relative_path": service.get_relative_template_path(output_path),
            },
            message="Région découpée avec succès",
        )

    except FileNotFoundError as e:
        return APIResponse(
            success=False,
            error={
                "code": "FILE_NOT_FOUND",
                "message": str(e),
            },
        )
    except ValueError as e:
        return APIResponse(
            success=False,
            error={
                "code": "INVALID_REGION",
                "message": str(e),
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/info")
async def get_image_info(path: str) -> APIResponse:
    """Récupère les informations d'une image."""
    try:
        service = get_image_service()
        info = service.get_image_info(path)

        return APIResponse(
            success=True,
            data=info,
        )

    except FileNotFoundError:
        return APIResponse(
            success=False,
            error={
                "code": "FILE_NOT_FOUND",
                "message": f"Image non trouvée: {path}",
            },
        )


@router.delete("/cleanup")
async def cleanup_upload(path: str) -> APIResponse:
    """Supprime un fichier uploadé temporaire."""
    service = get_image_service()
    deleted = service.cleanup_upload(path)

    return APIResponse(
        success=deleted,
        message="Fichier supprimé" if deleted else "Fichier non trouvé ou non supprimable",
    )


@router.get("/templates-list")
async def list_templates() -> APIResponse:
    """Liste tous les templates disponibles dans le framework."""
    templates = []

    if FRAMEWORK_TEMPLATES_DIR.exists():
        for file_path in FRAMEWORK_TEMPLATES_DIR.rglob("*.png"):
            try:
                # Chemin relatif par rapport au dossier templates
                relative_path = file_path.relative_to(FRAMEWORK_TEMPLATES_DIR)
                templates.append({
                    "path": str(relative_path).replace("\\", "/"),
                    "name": file_path.name,
                    "folder": str(relative_path.parent).replace("\\", "/") if relative_path.parent != Path(".") else "",
                })
            except ValueError:
                pass

        # Ajouter aussi les .jpg
        for file_path in FRAMEWORK_TEMPLATES_DIR.rglob("*.jpg"):
            try:
                relative_path = file_path.relative_to(FRAMEWORK_TEMPLATES_DIR)
                templates.append({
                    "path": str(relative_path).replace("\\", "/"),
                    "name": file_path.name,
                    "folder": str(relative_path.parent).replace("\\", "/") if relative_path.parent != Path(".") else "",
                })
            except ValueError:
                pass

    # Trier par dossier puis par nom
    templates.sort(key=lambda t: (t["folder"], t["name"]))

    return APIResponse(
        success=True,
        data={
            "templates": templates,
            "base_path": str(FRAMEWORK_TEMPLATES_DIR),
        },
    )


@router.get("/templates/{path:path}")
async def serve_template(path: str):
    """Sert un template existant du framework."""
    # Décoder le chemin URL
    decoded_path = unquote(path)
    file_path = FRAMEWORK_TEMPLATES_DIR / decoded_path

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Template non trouvé")

    # Vérifier que le fichier est bien dans le dossier templates
    try:
        file_path.resolve().relative_to(FRAMEWORK_TEMPLATES_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Accès non autorisé")

    return FileResponse(file_path)


@router.post("/check-duplicates")
async def check_duplicates(
    image_path: str,
    exact_threshold: float = 0.95,
    similar_threshold: float = 0.85,
) -> APIResponse:
    """
    Vérifie si une image a des duplicatas parmi les templates existants.

    Args:
        image_path: Chemin de l'image à vérifier
        exact_threshold: Seuil pour considérer un duplicata exact (0-1)
        similar_threshold: Seuil pour considérer un template similaire (0-1)

    Returns:
        Liste des duplicatas et templates similaires trouvés
    """
    try:
        service = get_image_service()
        result = service.find_duplicates(
            image_path=image_path,
            exact_threshold=exact_threshold,
            similar_threshold=similar_threshold,
        )

        return APIResponse(
            success=True,
            data=result,
        )

    except FileNotFoundError:
        return APIResponse(
            success=False,
            error={
                "code": "FILE_NOT_FOUND",
                "message": f"Image non trouvée: {image_path}",
            },
        )
    except Exception as e:
        return APIResponse(
            success=False,
            error={
                "code": "CHECK_ERROR",
                "message": str(e),
            },
        )


@router.get("/hash")
async def get_image_hash(path: str) -> APIResponse:
    """
    Calcule le hash perceptuel (dHash) d'une image.

    Args:
        path: Chemin de l'image

    Returns:
        Hash hexadécimal de l'image
    """
    try:
        service = get_image_service()
        hash_value = service.compute_dhash(path)

        return APIResponse(
            success=True,
            data={
                "path": path,
                "hash": hash_value,
            },
        )

    except FileNotFoundError:
        return APIResponse(
            success=False,
            error={
                "code": "FILE_NOT_FOUND",
                "message": f"Image non trouvée: {path}",
            },
        )
    except Exception as e:
        return APIResponse(
            success=False,
            error={
                "code": "HASH_ERROR",
                "message": str(e),
            },
        )
