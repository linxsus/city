"""Routes API pour la base de données du générateur."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ...models.schemas import APIResponse
from ...services.database_service import get_database_service


router = APIRouter(prefix="/db", tags=["Database"])


# === Schemas ===

class SessionCreate(BaseModel):
    """Données pour créer/mettre à jour une session."""
    type: str = Field(..., description="Type de session (etat, chemin, action_longue)")
    name: str = Field(..., description="Nom de l'élément")
    data: dict = Field(..., description="Données de la session")


class SessionUpdate(BaseModel):
    """Données pour mettre à jour une session."""
    name: str | None = Field(None, description="Nouveau nom")
    data: dict | None = Field(None, description="Nouvelles données")


class GroupCreate(BaseModel):
    """Données pour créer un groupe."""
    name: str = Field(..., description="Nom du groupe")
    description: str | None = Field(None, description="Description")
    color: str | None = Field(None, description="Couleur (hex)")


# === Sessions (Brouillons) ===

@router.get("/sessions")
async def list_sessions(
    session_type: str | None = None,
    include_completed: bool = False,
) -> APIResponse:
    """Liste les sessions (brouillons) sauvegardées."""
    service = get_database_service()
    sessions = service.list_sessions(
        session_type=session_type,
        include_completed=include_completed,
    )

    return APIResponse(
        success=True,
        data={
            "count": len(sessions),
            "sessions": sessions,
        },
    )


@router.get("/sessions/{session_id}")
async def get_session(session_id: int) -> APIResponse:
    """Récupère une session par son ID."""
    service = get_database_service()
    session = service.get_session(session_id)

    if session is None:
        return APIResponse(
            success=False,
            error={
                "code": "NOT_FOUND",
                "message": f"Session {session_id} non trouvée",
            },
        )

    return APIResponse(
        success=True,
        data=session,
    )


@router.post("/sessions")
async def create_session(data: SessionCreate) -> APIResponse:
    """Crée une nouvelle session."""
    service = get_database_service()
    session_id = service.save_session(
        session_type=data.type,
        name=data.name,
        data=data.data,
    )

    return APIResponse(
        success=True,
        data={"id": session_id},
        message="Session créée avec succès",
    )


@router.put("/sessions/{session_id}")
async def update_session(session_id: int, data: SessionCreate) -> APIResponse:
    """Met à jour une session existante."""
    service = get_database_service()

    # Vérifier que la session existe
    existing = service.get_session(session_id)
    if existing is None:
        return APIResponse(
            success=False,
            error={
                "code": "NOT_FOUND",
                "message": f"Session {session_id} non trouvée",
            },
        )

    service.save_session(
        session_type=data.type,
        name=data.name,
        data=data.data,
        session_id=session_id,
    )

    return APIResponse(
        success=True,
        message="Session mise à jour",
    )


@router.post("/sessions/{session_id}/complete")
async def complete_session(session_id: int) -> APIResponse:
    """Marque une session comme complétée."""
    service = get_database_service()
    success = service.complete_session(session_id)

    if not success:
        return APIResponse(
            success=False,
            error={
                "code": "NOT_FOUND",
                "message": f"Session {session_id} non trouvée",
            },
        )

    return APIResponse(
        success=True,
        message="Session marquée comme complétée",
    )


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: int) -> APIResponse:
    """Supprime une session."""
    service = get_database_service()
    success = service.delete_session(session_id)

    if not success:
        return APIResponse(
            success=False,
            error={
                "code": "NOT_FOUND",
                "message": f"Session {session_id} non trouvée",
            },
        )

    return APIResponse(
        success=True,
        message="Session supprimée",
    )


# === Groupes ===

@router.get("/groups")
async def list_groups() -> APIResponse:
    """Liste tous les groupes enregistrés."""
    service = get_database_service()
    groups = service.list_groups()

    return APIResponse(
        success=True,
        data={
            "count": len(groups),
            "groups": groups,
        },
    )


@router.post("/groups")
async def create_group(data: GroupCreate) -> APIResponse:
    """Crée un nouveau groupe."""
    service = get_database_service()
    group_id = service.save_group(
        name=data.name,
        description=data.description,
        color=data.color,
    )

    return APIResponse(
        success=True,
        data={"id": group_id, "name": data.name},
        message="Groupe créé avec succès",
    )


@router.delete("/groups/{name}")
async def delete_group(name: str) -> APIResponse:
    """Supprime un groupe."""
    service = get_database_service()
    success = service.delete_group(name)

    if not success:
        return APIResponse(
            success=False,
            error={
                "code": "NOT_FOUND",
                "message": f"Groupe '{name}' non trouvé",
            },
        )

    return APIResponse(
        success=True,
        message="Groupe supprimé",
    )


# === Templates Hash ===

@router.get("/templates")
async def list_template_hashes(source: str | None = None) -> APIResponse:
    """Liste les hashes de templates enregistrés."""
    service = get_database_service()
    templates = service.list_templates(source=source)

    return APIResponse(
        success=True,
        data={
            "count": len(templates),
            "templates": templates,
        },
    )


@router.get("/templates/search")
async def search_templates_by_hash(
    dhash: str,
    max_distance: int = 5,
) -> APIResponse:
    """Recherche des templates par hash perceptuel."""
    service = get_database_service()
    results = service.find_templates_by_hash(dhash, max_distance)

    return APIResponse(
        success=True,
        data={
            "count": len(results),
            "templates": results,
        },
    )


# === Historique ===

@router.get("/history")
async def list_generation_history(
    gen_type: str | None = None,
    limit: int = 50,
) -> APIResponse:
    """Liste l'historique des générations."""
    service = get_database_service()
    history = service.list_generation_history(gen_type=gen_type, limit=limit)

    return APIResponse(
        success=True,
        data={
            "count": len(history),
            "history": history,
        },
    )


# === Recherche et Stats ===

@router.get("/search")
async def search_database(
    q: str,
    tables: str | None = None,
) -> APIResponse:
    """
    Recherche globale dans la base de données.

    Args:
        q: Terme de recherche
        tables: Tables à rechercher (comma-separated: sessions,templates,groups,known_errors)
    """
    service = get_database_service()

    table_list = None
    if tables:
        table_list = [t.strip() for t in tables.split(",")]

    results = service.search(q, tables=table_list)

    return APIResponse(
        success=True,
        data=results,
    )


@router.get("/stats")
async def get_database_stats() -> APIResponse:
    """Retourne des statistiques sur la base de données."""
    service = get_database_service()
    stats = service.get_stats()

    return APIResponse(
        success=True,
        data=stats,
    )
