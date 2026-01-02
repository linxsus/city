"""Service d'intégration avec l'API Claude."""

import base64
import json
import re
from pathlib import Path

from ..config import (
    ANTHROPIC_API_KEY,
    CLAUDE_MAX_TOKENS,
    CLAUDE_MODEL,
    is_claude_available,
)
from ..models.schemas import SuggestionIA

# Import conditionnel d'Anthropic
try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    Anthropic = None


class ClaudeService:
    """Service d'intégration avec l'API Claude pour l'analyse d'images."""

    def __init__(self):
        self.client = None
        self.available = False

        if ANTHROPIC_AVAILABLE and is_claude_available():
            try:
                self.client = Anthropic(api_key=ANTHROPIC_API_KEY)
                self.available = True
            except Exception:
                pass

    def is_available(self) -> bool:
        """Vérifie si le service Claude est disponible."""
        return self.available

    def _encode_image(self, image_path: str | Path) -> str:
        """Encode une image en base64."""
        with open(image_path, "rb") as f:
            return base64.standard_b64encode(f.read()).decode("utf-8")

    def _get_media_type(self, image_path: str | Path) -> str:
        """Détermine le type MIME de l'image."""
        path = Path(image_path)
        suffix = path.suffix.lower()
        media_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        return media_types.get(suffix, "image/png")

    def _parse_json_response(self, text: str) -> dict:
        """Parse une réponse JSON de Claude."""
        # Chercher un bloc JSON dans la réponse
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        return {}

    async def analyser_image(
        self,
        image_path: str | Path,
        contexte: str | None = None,
        groupes_existants: list[str] | None = None,
    ) -> SuggestionIA:
        """
        Analyse une image et suggère les zones caractéristiques.

        Args:
            image_path: Chemin vers l'image à analyser
            contexte: Description optionnelle du contexte
            groupes_existants: Liste des groupes existants

        Returns:
            SuggestionIA avec les suggestions de régions, textes, groupes, priorités
        """
        if not self.available:
            return SuggestionIA(
                explication="API Claude non disponible. Mode manuel activé."
            )

        image_data = self._encode_image(image_path)
        media_type = self._get_media_type(image_path)

        prompt = self._build_analysis_prompt(contexte, groupes_existants)

        try:
            response = self.client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=CLAUDE_MAX_TOKENS,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_data,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt,
                            },
                        ],
                    }
                ],
            )

            result = self._parse_json_response(response.content[0].text)
            return SuggestionIA(
                regions=result.get("regions", []),
                textes=result.get("textes", []),
                groupe_suggere=result.get("groupe_suggere"),
                priorite_suggeree=result.get("priorite", 0),
                explication=result.get("explication"),
            )

        except Exception as e:
            return SuggestionIA(
                explication=f"Erreur API Claude: {e}"
            )

    async def detecter_boutons(
        self,
        image_path: str | Path,
    ) -> list[dict]:
        """
        Détecte les zones cliquables dans une image.

        Args:
            image_path: Chemin vers l'image

        Returns:
            Liste de régions cliquables avec descriptions
        """
        if not self.available:
            return []

        image_data = self._encode_image(image_path)
        media_type = self._get_media_type(image_path)

        prompt = """Analyse cette capture d'écran de jeu mobile et identifie toutes les zones cliquables (boutons, icônes, liens).

Pour chaque zone cliquable, donne:
- Les coordonnées (x, y, width, height) en pixels
- Une description de ce que fait le bouton
- Un nom suggéré pour le template

Réponds en JSON:
{
  "boutons": [
    {
      "x": int,
      "y": int,
      "width": int,
      "height": int,
      "description": "string",
      "nom_suggere": "string"
    }
  ]
}"""

        try:
            response = self.client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=CLAUDE_MAX_TOKENS,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_data,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt,
                            },
                        ],
                    }
                ],
            )

            result = self._parse_json_response(response.content[0].text)
            return result.get("boutons", [])

        except Exception:
            return []

    async def suggerer_erreurs(
        self,
        action_description: str,
        erreurs_disponibles: list[dict],
    ) -> dict:
        """
        Suggère des erreurs pertinentes pour une action.

        Args:
            action_description: Description de l'action
            erreurs_disponibles: Liste des erreurs disponibles

        Returns:
            Dict avec erreurs_verif_apres, erreurs_si_echec suggérées
        """
        if not self.available:
            return {
                "erreurs_verif_apres": [],
                "erreurs_si_echec": [],
                "explication": "API Claude non disponible",
            }

        # Préparer la liste des erreurs pour le prompt
        erreurs_str = "\n".join([
            f"- {e['nom']}: {e['message']} (catégorie: {e.get('categorie', 'autre')}, retry: {e.get('retry_action_originale', False)})"
            for e in erreurs_disponibles
        ])

        prompt = f"""Tu es un assistant pour un framework d'automatisation de jeu mobile.

Voici la description d'une action:
{action_description}

Voici les erreurs disponibles dans le système:
{erreurs_str}

Suggère les erreurs les plus pertinentes pour cette action:

1. **erreurs_verif_apres** - Erreurs à vérifier après chaque exécution réussie (popups intempestifs, déconnexions)

2. **erreurs_si_echec** - Erreurs à vérifier si l'action échoue (manque de ressources, slots pleins, etc.)

Réponds UNIQUEMENT en JSON valide:
{{
  "erreurs_verif_apres": ["nom_erreur1", "nom_erreur2"],
  "erreurs_si_echec": ["nom_erreur3", "nom_erreur4"],
  "explication": "Pourquoi ces erreurs sont pertinentes"
}}"""

        try:
            response = self.client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=CLAUDE_MAX_TOKENS,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            )

            result = self._parse_json_response(response.content[0].text)
            return {
                "erreurs_verif_apres": result.get("erreurs_verif_apres", []),
                "erreurs_si_echec": result.get("erreurs_si_echec", []),
                "explication": result.get("explication", ""),
            }

        except Exception as e:
            return {
                "erreurs_verif_apres": [],
                "erreurs_si_echec": [],
                "explication": f"Erreur API Claude: {e}",
            }

    def _build_analysis_prompt(
        self,
        contexte: str | None,
        groupes_existants: list[str] | None,
    ) -> str:
        """Construit le prompt d'analyse d'image."""
        groupes_str = ""
        if groupes_existants:
            groupes_str = f"\n\nGroupes existants dans le projet: {', '.join(groupes_existants)}"

        contexte_str = ""
        if contexte:
            contexte_str = f"\n\nContexte additionnel: {contexte}"

        return f"""Analyse cette capture d'écran d'un jeu mobile (Mafia City).

Identifie:

1. **Zone caractéristique** - Une zone rectangulaire unique et stable pour identifier cet écran
   - Coordonnées (x, y, largeur, hauteur) en pixels
   - Pourquoi cette zone est distinctive

2. **Textes visibles** - Les textes importants qui pourraient identifier cet écran

3. **Type d'écran** - Menu, popup, écran de jeu, chargement, etc.
   - Suggère un groupe approprié{groupes_str}

4. **Priorité** - 0 pour écran normal, 80-100 pour popups/erreurs

Réponds UNIQUEMENT en JSON valide:
{{
  "regions": [
    {{
      "x": int,
      "y": int,
      "width": int,
      "height": int,
      "description": "string",
      "confidence": float
    }}
  ],
  "textes": ["string"],
  "type_ecran": "string",
  "groupe_suggere": "string",
  "priorite": int,
  "explication": "string"
}}{contexte_str}"""


# Singleton
_claude_service: ClaudeService | None = None


def get_claude_service() -> ClaudeService:
    """Retourne l'instance singleton du service Claude."""
    global _claude_service
    if _claude_service is None:
        _claude_service = ClaudeService()
    return _claude_service
