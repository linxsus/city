"""Service de gestion des chemins."""

from ..config import GENERATED_DIR, get_existing_states
from ..models.schemas import CheminCreate, CheminSchema
from .etat_service import snake_to_pascal


class CheminService:
    """Service pour la création et gestion des chemins."""

    def __init__(self):
        self.chemins_dir = GENERATED_DIR / "chemins"
        self.chemins_dir.mkdir(parents=True, exist_ok=True)

    def get_existing_states(self) -> list[str]:
        """Récupère les états existants pour les listes déroulantes."""
        return get_existing_states()

    def create_chemin(self, data: CheminCreate) -> CheminSchema:
        """
        Crée un nouveau chemin.

        Args:
            data: Données du chemin à créer

        Returns:
            CheminSchema complet
        """
        # Générer le nom de classe
        # Format: CheminEtatInitialVersEtatSortie
        nom_classe = f"Chemin{snake_to_pascal(data.etat_initial)}Vers{snake_to_pascal(data.etat_sortie)}"

        chemin = CheminSchema(
            nom=data.nom,
            nom_classe=nom_classe,
            etat_initial=data.etat_initial,
            etat_sortie=data.etat_sortie,
            etats_sortie_possibles=data.etats_sortie_possibles,
            actions=data.actions,
            description=data.description,
        )

        return chemin

    def validate_chemin(self, data: CheminCreate) -> list[str]:
        """
        Valide les données d'un chemin.

        Args:
            data: Données à valider

        Returns:
            Liste des erreurs (vide si valide)
        """
        errors = []
        existing_states = self.get_existing_states()

        # Vérifier l'état initial
        if data.etat_initial not in existing_states:
            errors.append(
                f"État initial '{data.etat_initial}' non trouvé. "
                f"États disponibles: {', '.join(existing_states)}"
            )

        # Vérifier l'état de sortie
        if data.etat_sortie not in existing_states:
            errors.append(
                f"État de sortie '{data.etat_sortie}' non trouvé. "
                f"États disponibles: {', '.join(existing_states)}"
            )

        # Vérifier les états de sortie possibles
        for etat in data.etats_sortie_possibles:
            if etat not in existing_states:
                errors.append(
                    f"État de sortie possible '{etat}' non trouvé"
                )

        # Vérifier qu'il y a au moins une action
        if not data.actions:
            errors.append("Au moins une action est requise")

        return errors

    def suggest_exit_states(self, etat_sortie: str) -> list[str]:
        """
        Suggère des états de sortie possibles basés sur l'état de sortie principal.

        Args:
            etat_sortie: État de sortie principal

        Returns:
            Liste des états de sortie suggérés (popups, erreurs)
        """
        existing_states = self.get_existing_states()

        # Suggérer les popups et erreurs courants
        suggestions = []

        popup_patterns = ["popup_", "erreur_", "error_"]
        for state in existing_states:
            for pattern in popup_patterns:
                if state.startswith(pattern) and state != etat_sortie:
                    suggestions.append(state)
                    break

        return suggestions


# Singleton
_chemin_service: CheminService | None = None


def get_chemin_service() -> CheminService:
    """Retourne l'instance singleton du service chemin."""
    global _chemin_service
    if _chemin_service is None:
        _chemin_service = CheminService()
    return _chemin_service
