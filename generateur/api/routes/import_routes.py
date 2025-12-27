"""Routes API pour l'import et la visualisation des éléments existants."""

import shutil
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter

from ...config import FRAMEWORK_CHEMINS_DIR, FRAMEWORK_ETATS_DIR, FRAMEWORK_TEMPLATES_DIR, TRASH_DIR
from ...models.schemas import APIResponse
from ...services.import_service import get_import_service

router = APIRouter(prefix="/import", tags=["Import"])


@router.get("/summary")
async def get_summary() -> APIResponse:
    """Récupère un résumé de tous les éléments existants."""
    service = get_import_service()
    summary = service.get_summary()

    return APIResponse(
        success=True,
        data=summary,
    )


@router.get("/etats")
async def get_all_etats() -> APIResponse:
    """Liste tous les états existants."""
    service = get_import_service()
    etats = service.get_all_etats()

    return APIResponse(
        success=True,
        data={
            "count": len(etats),
            "etats": [e.to_dict() for e in etats],
        },
    )


@router.get("/etats/{nom}")
async def get_etat_by_name(nom: str) -> APIResponse:
    """Récupère un état par son nom."""
    service = get_import_service()
    etat = service.get_etat_by_name(nom)

    if etat is None:
        return APIResponse(
            success=False,
            error={
                "code": "NOT_FOUND",
                "message": f"État '{nom}' non trouvé",
            },
        )

    return APIResponse(
        success=True,
        data=etat.to_dict(),
    )


@router.get("/chemins")
async def get_all_chemins() -> APIResponse:
    """Liste tous les chemins existants."""
    service = get_import_service()
    chemins = service.get_all_chemins()

    return APIResponse(
        success=True,
        data={
            "count": len(chemins),
            "chemins": [c.to_dict() for c in chemins],
        },
    )


@router.get("/chemins/{nom}")
async def get_chemin_by_name(nom: str) -> APIResponse:
    """Récupère un chemin par son nom."""
    service = get_import_service()
    chemin = service.get_chemin_by_name(nom)

    if chemin is None:
        return APIResponse(
            success=False,
            error={
                "code": "NOT_FOUND",
                "message": f"Chemin '{nom}' non trouvé",
            },
        )

    return APIResponse(
        success=True,
        data=chemin.to_dict(),
    )


@router.get("/actions")
async def get_all_actions() -> APIResponse:
    """Liste toutes les actions existantes."""
    service = get_import_service()
    actions = service.get_all_actions()

    return APIResponse(
        success=True,
        data={
            "count": len(actions),
            "actions": [a.to_dict() for a in actions],
        },
    )


@router.get("/actions/{nom}")
async def get_action_by_name(nom: str) -> APIResponse:
    """Récupère une action par son nom."""
    service = get_import_service()
    action = service.get_action_by_name(nom)

    if action is None:
        return APIResponse(
            success=False,
            error={
                "code": "NOT_FOUND",
                "message": f"Action '{nom}' non trouvée",
            },
        )

    return APIResponse(
        success=True,
        data=action.to_dict(),
    )


@router.get("/templates")
async def get_all_templates() -> APIResponse:
    """Liste tous les templates existants."""
    service = get_import_service()
    templates = service.get_all_templates()

    return APIResponse(
        success=True,
        data={
            "count": len(templates),
            "templates": templates,
        },
    )


@router.get("/templates/usage")
async def get_template_usage(path: str) -> APIResponse:
    """Trouve où un template est utilisé."""
    service = get_import_service()
    usage = service.get_template_usage(path)

    return APIResponse(
        success=True,
        data=usage,
    )


@router.get("/templates/orphans")
async def get_orphan_templates() -> APIResponse:
    """Liste les templates non utilisés."""
    service = get_import_service()
    orphans = service.find_orphan_templates()

    return APIResponse(
        success=True,
        data={
            "count": len(orphans),
            "orphans": orphans,
        },
    )


@router.get("/templates/missing")
async def get_missing_templates() -> APIResponse:
    """Liste les templates référencés mais inexistants."""
    service = get_import_service()
    missing = service.find_missing_templates()

    return APIResponse(
        success=True,
        data={
            "count": len(missing),
            "missing": missing,
        },
    )


@router.get("/groupes")
async def get_all_groupes() -> APIResponse:
    """Liste tous les groupes utilisés."""
    service = get_import_service()
    summary = service.get_summary()

    return APIResponse(
        success=True,
        data={
            "groupes": summary["groupes"],
        },
    )


def _move_to_trash(file_path: Path, element_type: str) -> Path:
    """Déplace un fichier vers la corbeille."""
    # Créer un sous-dossier par type et par date
    date_str = datetime.now().strftime("%Y%m%d")
    trash_subdir = TRASH_DIR / element_type / date_str
    trash_subdir.mkdir(parents=True, exist_ok=True)

    # Nom unique avec timestamp
    timestamp = datetime.now().strftime("%H%M%S")
    new_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
    trash_path = trash_subdir / new_name

    shutil.move(str(file_path), str(trash_path))
    return trash_path


@router.delete("/etats/{nom}")
async def delete_etat(nom: str) -> APIResponse:
    """Supprime un état (le déplace vers la corbeille)."""
    service = get_import_service()
    etat = service.get_etat_by_name(nom)

    if etat is None:
        return APIResponse(
            success=False,
            error={
                "code": "NOT_FOUND",
                "message": f"État '{nom}' non trouvé",
            },
        )

    file_path = Path(etat.fichier)
    if not file_path.exists():
        return APIResponse(
            success=False,
            error={
                "code": "FILE_NOT_FOUND",
                "message": f"Fichier '{etat.fichier}' non trouvé",
            },
        )

    try:
        trash_path = _move_to_trash(file_path, "etats")
        return APIResponse(
            success=True,
            message=f"État '{nom}' déplacé vers la corbeille",
            data={
                "nom": nom,
                "original_path": str(file_path),
                "trash_path": str(trash_path),
            },
        )
    except Exception as e:
        return APIResponse(
            success=False,
            error={
                "code": "DELETE_ERROR",
                "message": f"Erreur lors de la suppression: {str(e)}",
            },
        )


@router.delete("/chemins/{nom}")
async def delete_chemin(nom: str) -> APIResponse:
    """Supprime un chemin (le déplace vers la corbeille)."""
    service = get_import_service()
    chemin = service.get_chemin_by_name(nom)

    if chemin is None:
        return APIResponse(
            success=False,
            error={
                "code": "NOT_FOUND",
                "message": f"Chemin '{nom}' non trouvé",
            },
        )

    file_path = Path(chemin.fichier)
    if not file_path.exists():
        return APIResponse(
            success=False,
            error={
                "code": "FILE_NOT_FOUND",
                "message": f"Fichier '{chemin.fichier}' non trouvé",
            },
        )

    try:
        trash_path = _move_to_trash(file_path, "chemins")
        return APIResponse(
            success=True,
            message=f"Chemin '{nom}' déplacé vers la corbeille",
            data={
                "nom": nom,
                "original_path": str(file_path),
                "trash_path": str(trash_path),
            },
        )
    except Exception as e:
        return APIResponse(
            success=False,
            error={
                "code": "DELETE_ERROR",
                "message": f"Erreur lors de la suppression: {str(e)}",
            },
        )


@router.delete("/templates")
async def delete_template(path: str) -> APIResponse:
    """Supprime un template (le déplace vers la corbeille)."""
    file_path = FRAMEWORK_TEMPLATES_DIR / path

    if not file_path.exists():
        return APIResponse(
            success=False,
            error={
                "code": "NOT_FOUND",
                "message": f"Template '{path}' non trouvé",
            },
        )

    # Vérifier que le fichier est bien dans le dossier templates
    try:
        file_path.resolve().relative_to(FRAMEWORK_TEMPLATES_DIR.resolve())
    except ValueError:
        return APIResponse(
            success=False,
            error={
                "code": "INVALID_PATH",
                "message": "Chemin non autorisé",
            },
        )

    try:
        trash_path = _move_to_trash(file_path, "templates")
        return APIResponse(
            success=True,
            message=f"Template '{path}' déplacé vers la corbeille",
            data={
                "path": path,
                "original_path": str(file_path),
                "trash_path": str(trash_path),
            },
        )
    except Exception as e:
        return APIResponse(
            success=False,
            error={
                "code": "DELETE_ERROR",
                "message": f"Erreur lors de la suppression: {str(e)}",
            },
        )
