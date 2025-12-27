"""Schémas Pydantic pour ActionLongue."""

from datetime import datetime

from pydantic import BaseModel, Field


class ActionLongueCreate(BaseModel):
    """Données pour créer une ActionLongue."""
    nom: str = Field(
        ...,
        min_length=1,
        max_length=100,
        pattern=r'^[a-z][a-z0-9_]*$',
        description="Nom de l'action (snake_case)"
    )
    etat_requis: str | None = Field(
        default=None,
        description="État requis pour exécuter l'action"
    )
    description: str | None = Field(
        default=None,
        description="Description de l'action"
    )
    code_genere: str = Field(
        ...,
        description="Code Python généré par Blockly"
    )
    blockly_workspace: str = Field(
        ...,
        description="XML du workspace Blockly (pour sauvegarde)"
    )


class ActionLongueSchema(ActionLongueCreate):
    """ActionLongue complète avec métadonnées."""
    fichier_genere: str | None = Field(
        default=None,
        description="Chemin du fichier Python généré"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Date de création"
    )
