"""Service de gestion des actions."""

from ..generators.action_generator import ActionGenerator
from ..generators.action_longue_generator import ActionLongueGenerator
from ..models.schemas import (
    ActionCreate,
    ActionLongueCreate,
    ActionLongueSchema,
    ActionSchema,
)


def to_class_name(nom: str, prefix: str = "Action") -> str:
    """Convertit un nom snake_case en PascalCase avec préfixe."""
    parts = nom.split("_")
    pascal = "".join(p.capitalize() for p in parts)
    return f"{prefix}{pascal}"


class ActionService:
    """Service pour créer et gérer les actions simples."""

    def __init__(self):
        self.generator = ActionGenerator()

    def create_action(self, data: ActionCreate) -> ActionSchema:
        """
        Crée une nouvelle action.

        Args:
            data: Données de création

        Returns:
            Schéma de l'action créée
        """
        action = ActionSchema(
            **data.model_dump(),
            nom_classe=to_class_name(data.nom),
        )
        return action

    def preview(self, data: ActionCreate) -> dict:
        """
        Prévisualise le code généré.

        Args:
            data: Données de l'action

        Returns:
            Dict avec le code et métadonnées
        """
        action = self.create_action(data)
        return self.generator.preview(action)

    def save(self, data: ActionCreate) -> dict:
        """
        Sauvegarde l'action.

        Args:
            data: Données de l'action

        Returns:
            Dict avec le résultat
        """
        action = self.create_action(data)
        filepath = self.generator.save(action)

        return {
            "filepath": str(filepath),
            "class_name": action.nom_classe,
            "code": self.generator.generate(action),
        }


class ActionLongueService:
    """Service pour créer et gérer les actions longues."""

    def __init__(self):
        self.generator = ActionLongueGenerator()

    def create_action_longue(self, data: ActionLongueCreate) -> ActionLongueSchema:
        """
        Crée une nouvelle action longue.

        Args:
            data: Données de création

        Returns:
            Schéma de l'action longue créée
        """
        action = ActionLongueSchema(
            **data.model_dump(),
            nom_classe=to_class_name(data.nom),
        )
        return action

    def preview(self, data: ActionLongueCreate) -> dict:
        """
        Prévisualise le code généré.

        Args:
            data: Données de l'action longue

        Returns:
            Dict avec le code et métadonnées
        """
        action = self.create_action_longue(data)
        return self.generator.preview(action)

    def save(self, data: ActionLongueCreate) -> dict:
        """
        Sauvegarde l'action longue.

        Args:
            data: Données de l'action longue

        Returns:
            Dict avec le résultat
        """
        action = self.create_action_longue(data)
        filepath = self.generator.save(action)

        return {
            "filepath": str(filepath),
            "class_name": action.nom_classe,
            "code": self.generator.generate(action),
        }


# Singletons
_action_service: ActionService | None = None
_action_longue_service: ActionLongueService | None = None


def get_action_service() -> ActionService:
    """Retourne l'instance singleton du service action."""
    global _action_service
    if _action_service is None:
        _action_service = ActionService()
    return _action_service


def get_action_longue_service() -> ActionLongueService:
    """Retourne l'instance singleton du service action longue."""
    global _action_longue_service
    if _action_longue_service is None:
        _action_longue_service = ActionLongueService()
    return _action_longue_service
