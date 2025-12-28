"""Routes API pour la capture d'écran via scrcpy/ADB.

Ces endpoints permettent de capturer directement l'écran depuis un appareil
Android connecté, sans avoir besoin d'uploader manuellement des captures.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...models.schemas import APIResponse
from ...services.scrcpy_service import get_scrcpy_service

router = APIRouter(prefix="/scrcpy", tags=["Scrcpy/ADB"])


class ClickRequest(BaseModel):
    """Requête pour un clic sur l'appareil."""

    x: int
    y: int


class TemplateRequest(BaseModel):
    """Requête pour sauvegarder un template."""

    template_name: str
    subdir: str = "scrcpy"
    region_x: Optional[int] = None
    region_y: Optional[int] = None
    region_width: Optional[int] = None
    region_height: Optional[int] = None


@router.get("/status")
async def get_status() -> APIResponse:
    """Récupère le statut de la connexion ADB.

    Returns:
        - connected: bool - True si un appareil est connecté
        - devices: list - Liste des appareils détectés
        - device_serial: str - Serial de l'appareil sélectionné
        - device_name: str - Nom/modèle de l'appareil
        - screen_size: tuple - Dimensions de l'écran (largeur, hauteur)
    """
    try:
        service = get_scrcpy_service()
        status = service.get_status()

        return APIResponse(
            success=True,
            data=status,
        )
    except Exception as e:
        return APIResponse(
            success=False,
            error={
                "code": "ADB_ERROR",
                "message": f"Erreur ADB: {str(e)}",
            },
        )


@router.post("/capture")
async def capture_screen() -> APIResponse:
    """Capture l'écran de l'appareil et sauvegarde le fichier.

    L'image est sauvegardée dans le dossier uploads du générateur
    et peut être utilisée directement dans l'interface.

    Returns:
        - path: str - Chemin complet du fichier
        - filename: str - Nom du fichier
        - width: int - Largeur de l'image
        - height: int - Hauteur de l'image
        - size_bytes: int - Taille en octets
    """
    try:
        service = get_scrcpy_service()

        # Vérifier la connexion
        status = service.get_status()
        if not status["connected"]:
            return APIResponse(
                success=False,
                error={
                    "code": "NO_DEVICE",
                    "message": "Aucun appareil Android connecté",
                },
            )

        # Capturer l'écran
        result = service.capture_and_save(prefix="scrcpy")

        if not result:
            return APIResponse(
                success=False,
                error={
                    "code": "CAPTURE_FAILED",
                    "message": "Échec de la capture d'écran",
                },
            )

        return APIResponse(
            success=True,
            data=result,
            message=f"Capture réussie: {result['width']}x{result['height']}",
        )

    except Exception as e:
        return APIResponse(
            success=False,
            error={
                "code": "CAPTURE_ERROR",
                "message": f"Erreur capture: {str(e)}",
            },
        )


@router.get("/capture-preview")
async def capture_preview() -> APIResponse:
    """Capture l'écran et retourne une data URL pour affichage direct.

    Utile pour prévisualiser l'écran sans sauvegarder de fichier.

    Returns:
        - data_url: str - Image en base64 (data:image/png;base64,...)
        - width: int - Largeur de l'image
        - height: int - Hauteur de l'image
    """
    try:
        service = get_scrcpy_service()

        # Vérifier la connexion
        status = service.get_status()
        if not status["connected"]:
            return APIResponse(
                success=False,
                error={
                    "code": "NO_DEVICE",
                    "message": "Aucun appareil Android connecté",
                },
            )

        result = service.capture_to_base64()

        if not result:
            return APIResponse(
                success=False,
                error={
                    "code": "CAPTURE_FAILED",
                    "message": "Échec de la capture d'écran",
                },
            )

        return APIResponse(
            success=True,
            data=result,
        )

    except Exception as e:
        return APIResponse(
            success=False,
            error={
                "code": "CAPTURE_ERROR",
                "message": f"Erreur capture: {str(e)}",
            },
        )


@router.post("/save-template")
async def save_template(request: TemplateRequest) -> APIResponse:
    """Capture l'écran et sauvegarde directement comme template.

    Args:
        template_name: Nom du template (sans extension)
        subdir: Sous-dossier dans templates/ (défaut: "scrcpy")
        region_x, region_y, region_width, region_height: Région à extraire (optionnel)

    Returns:
        - path: str - Chemin complet du template
        - relative_path: str - Chemin relatif pour le code
        - filename: str - Nom du fichier
        - width: int - Largeur du template
        - height: int - Hauteur du template
    """
    try:
        service = get_scrcpy_service()

        # Vérifier la connexion
        status = service.get_status()
        if not status["connected"]:
            return APIResponse(
                success=False,
                error={
                    "code": "NO_DEVICE",
                    "message": "Aucun appareil Android connecté",
                },
            )

        # Construire la région si spécifiée
        region = None
        if all(
            v is not None
            for v in [
                request.region_x,
                request.region_y,
                request.region_width,
                request.region_height,
            ]
        ):
            region = (
                request.region_x,
                request.region_y,
                request.region_width,
                request.region_height,
            )

        result = service.save_for_template(
            template_name=request.template_name,
            subdir=request.subdir,
            region=region,
        )

        if not result:
            return APIResponse(
                success=False,
                error={
                    "code": "SAVE_FAILED",
                    "message": "Échec de la sauvegarde du template",
                },
            )

        return APIResponse(
            success=True,
            data=result,
            message=f"Template sauvegardé: {result['relative_path']}",
        )

    except Exception as e:
        return APIResponse(
            success=False,
            error={
                "code": "SAVE_ERROR",
                "message": f"Erreur sauvegarde: {str(e)}",
            },
        )


@router.post("/click")
async def click_at(request: ClickRequest) -> APIResponse:
    """Effectue un clic sur l'appareil aux coordonnées spécifiées.

    Args:
        x: Coordonnée X
        y: Coordonnée Y

    Returns:
        success: True si le clic a réussi
    """
    try:
        service = get_scrcpy_service()

        # Vérifier la connexion
        status = service.get_status()
        if not status["connected"]:
            return APIResponse(
                success=False,
                error={
                    "code": "NO_DEVICE",
                    "message": "Aucun appareil Android connecté",
                },
            )

        success = service.click_at(request.x, request.y)

        return APIResponse(
            success=success,
            message=f"Clic à ({request.x}, {request.y})" if success else "Échec du clic",
        )

    except Exception as e:
        return APIResponse(
            success=False,
            error={
                "code": "CLICK_ERROR",
                "message": f"Erreur clic: {str(e)}",
            },
        )


@router.post("/back")
async def press_back() -> APIResponse:
    """Appuie sur le bouton Retour de l'appareil."""
    try:
        service = get_scrcpy_service()
        success = service.press_back()

        return APIResponse(
            success=success,
            message="Bouton Retour pressé" if success else "Échec",
        )

    except Exception as e:
        return APIResponse(
            success=False,
            error={
                "code": "KEY_ERROR",
                "message": f"Erreur touche: {str(e)}",
            },
        )


@router.post("/home")
async def press_home() -> APIResponse:
    """Appuie sur le bouton Home de l'appareil."""
    try:
        service = get_scrcpy_service()
        success = service.press_home()

        return APIResponse(
            success=success,
            message="Bouton Home pressé" if success else "Échec",
        )

    except Exception as e:
        return APIResponse(
            success=False,
            error={
                "code": "KEY_ERROR",
                "message": f"Erreur touche: {str(e)}",
            },
        )


@router.post("/launch-scrcpy")
async def launch_scrcpy() -> APIResponse:
    """Lance scrcpy pour visualiser l'écran de l'appareil.

    Ouvre une fenêtre scrcpy si un appareil est connecté.
    """
    try:
        service = get_scrcpy_service()

        # Vérifier la connexion
        status = service.get_status()
        if not status["connected"]:
            return APIResponse(
                success=False,
                error={
                    "code": "NO_DEVICE",
                    "message": "Aucun appareil Android connecté",
                },
            )

        # Vérifier si déjà lancé
        if service.is_scrcpy_running():
            return APIResponse(
                success=True,
                message="Scrcpy est déjà en cours d'exécution",
            )

        success = service.launch_scrcpy_window()

        return APIResponse(
            success=success,
            message="Scrcpy lancé" if success else "Échec du lancement de scrcpy",
        )

    except Exception as e:
        return APIResponse(
            success=False,
            error={
                "code": "SCRCPY_ERROR",
                "message": f"Erreur scrcpy: {str(e)}",
            },
        )


@router.get("/scrcpy-status")
async def get_scrcpy_status() -> APIResponse:
    """Vérifie si scrcpy est en cours d'exécution."""
    try:
        service = get_scrcpy_service()
        running = service.is_scrcpy_running()

        return APIResponse(
            success=True,
            data={"running": running},
        )

    except Exception as e:
        return APIResponse(
            success=False,
            error={
                "code": "SCRCPY_ERROR",
                "message": f"Erreur vérification scrcpy: {str(e)}",
            },
        )
