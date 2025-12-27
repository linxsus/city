"""Service de gestion des ActionLongue."""

from pathlib import Path

from ..config import GENERATED_DIR
from ..models.schemas_action_longue import ActionLongueCreate, ActionLongueSchema


class ActionLongueService:
    """Service pour la création et gestion des ActionLongue."""

    def __init__(self):
        self.actions_dir = GENERATED_DIR / "actions_longues"
        self.actions_dir.mkdir(parents=True, exist_ok=True)

        self.workspaces_dir = GENERATED_DIR / "workspaces"
        self.workspaces_dir.mkdir(parents=True, exist_ok=True)

    def create_action_longue(self, data: ActionLongueCreate) -> ActionLongueSchema:
        """
        Crée une nouvelle ActionLongue.

        Args:
            data: Données de l'action à créer

        Returns:
            ActionLongueSchema avec le chemin du fichier généré
        """
        # Sauvegarder le code Python
        filename = f"action_longue_{data.nom}.py"
        filepath = self.actions_dir / filename
        filepath.write_text(data.code_genere, encoding="utf-8")

        # Sauvegarder le workspace Blockly (pour pouvoir le recharger)
        workspace_file = self.workspaces_dir / f"{data.nom}.xml"
        workspace_file.write_text(data.blockly_workspace, encoding="utf-8")

        return ActionLongueSchema(
            nom=data.nom,
            etat_requis=data.etat_requis,
            description=data.description,
            code_genere=data.code_genere,
            blockly_workspace=data.blockly_workspace,
            fichier_genere=str(filepath),
        )

    def validate_action_longue(self, data: ActionLongueCreate) -> list[str]:
        """
        Valide les données d'une ActionLongue.

        Args:
            data: Données à valider

        Returns:
            Liste des erreurs (vide si valide)
        """
        errors = []

        # Vérifier que le code n'est pas vide
        if not data.code_genere or len(data.code_genere.strip()) < 50:
            errors.append("Le code généré semble vide ou incomplet")

        # Vérifier que le nom n'existe pas déjà
        existing_file = self.actions_dir / f"action_longue_{data.nom}.py"
        if existing_file.exists():
            errors.append(f"Une ActionLongue avec le nom '{data.nom}' existe déjà")

        return errors

    def get_workspace(self, nom: str) -> str | None:
        """
        Récupère le workspace Blockly d'une ActionLongue existante.

        Args:
            nom: Nom de l'action

        Returns:
            XML du workspace ou None si non trouvé
        """
        workspace_file = self.workspaces_dir / f"{nom}.xml"
        if workspace_file.exists():
            return workspace_file.read_text(encoding="utf-8")
        return None

    def list_actions(self) -> list[dict]:
        """
        Liste toutes les ActionLongue existantes.

        Returns:
            Liste des actions avec leurs métadonnées
        """
        actions = []

        for file in self.actions_dir.glob("action_longue_*.py"):
            nom = file.stem.replace("action_longue_", "")
            workspace_exists = (self.workspaces_dir / f"{nom}.xml").exists()

            actions.append({
                "nom": nom,
                "fichier": str(file),
                "workspace_disponible": workspace_exists,
            })

        return actions


# Singleton
_action_longue_service: ActionLongueService | None = None


def get_action_longue_service() -> ActionLongueService:
    """Retourne l'instance singleton du service ActionLongue."""
    global _action_longue_service
    if _action_longue_service is None:
        _action_longue_service = ActionLongueService()
    return _action_longue_service
