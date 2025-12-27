"""Générateur de code pour les chemins."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from ..config import GENERATED_DIR
from ..models.schemas import ActionReference, CheminSchema


class CheminGenerator:
    """Génère le code Python pour les classes Chemin."""

    def __init__(self):
        templates_dir = Path(__file__).parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(templates_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.template = self.env.get_template("chemin.py.j2")
        self.output_dir = GENERATED_DIR / "chemins"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _generate_action_code(self, action: ActionReference) -> str:
        """
        Génère le code Python pour une action.

        Args:
            action: Référence de l'action

        Returns:
            Code Python de l'action
        """
        params = action.parametres

        if action.type == "ActionBouton":
            template_path = params.get("template_path", "")
            threshold = params.get("threshold", 0.8)
            offset_x = params.get("offset_x", 0)
            offset_y = params.get("offset_y", 0)

            if offset_x or offset_y:
                return (
                    f'ActionBouton(manoir, "{template_path}", '
                    f"threshold={threshold}, offset=({offset_x}, {offset_y}))"
                )
            else:
                return f'ActionBouton(manoir, "{template_path}", threshold={threshold})'

        elif action.type == "ActionAttendre":
            duree = params.get("duree", 1)
            return f"ActionAttendre(manoir, {duree})"

        elif action.type == "ActionTexte":
            texte = params.get("texte_recherche", "")
            offset_x = params.get("offset_x", 0)
            offset_y = params.get("offset_y", 0)

            if offset_x or offset_y:
                return (
                    f'ActionTexte(manoir, "{texte}", '
                    f"offset=({offset_x}, {offset_y}))"
                )
            else:
                return f'ActionTexte(manoir, "{texte}")'

        else:
            return f"# TODO: {action.type} non supporté"

    def _get_imports(self, actions: list[ActionReference]) -> list[str]:
        """
        Détermine les imports nécessaires selon les actions.

        Args:
            actions: Liste des actions

        Returns:
            Liste des lignes d'import
        """
        imports = set()

        for action in actions:
            if action.type == "ActionBouton":
                imports.add("from actions.simple.action_bouton import ActionBouton")
            elif action.type == "ActionAttendre":
                imports.add("from actions.simple.action_attendre import ActionAttendre")
            elif action.type == "ActionTexte":
                imports.add("from actions.simple.action_texte import ActionTexte")

        return sorted(imports)

    def generate(self, chemin: CheminSchema) -> str:
        """
        Génère le code Python pour un chemin.

        Args:
            chemin: Schéma du chemin à générer

        Returns:
            Code Python généré
        """
        # Préparer les actions avec leur code
        actions_with_code = []
        for action in chemin.actions:
            actions_with_code.append({
                "type": action.type,
                "code": self._generate_action_code(action),
            })

        # Liste complète des états de sortie
        etats_sortie_tous = [chemin.etat_sortie] + chemin.etats_sortie_possibles

        return self.template.render(
            nom_classe=chemin.nom_classe,
            etat_initial=chemin.etat_initial,
            etat_sortie=chemin.etat_sortie,
            etats_sortie_possibles=chemin.etats_sortie_possibles,
            etats_sortie_tous=etats_sortie_tous,
            actions=actions_with_code,
            imports=self._get_imports(chemin.actions),
            description=chemin.description or "",
        )

    def save(self, chemin: CheminSchema) -> Path:
        """
        Sauvegarde le code généré dans un fichier.

        Args:
            chemin: Schéma du chemin

        Returns:
            Chemin du fichier créé
        """
        code = self.generate(chemin)

        # Nom du fichier basé sur les états
        filename = f"chemin_{chemin.etat_initial}_vers_{chemin.etat_sortie}.py"
        filepath = self.output_dir / filename
        filepath.write_text(code, encoding="utf-8")

        chemin.fichier_genere = str(filepath)

        return filepath

    def preview(self, chemin: CheminSchema) -> dict:
        """
        Génère une prévisualisation du code.

        Args:
            chemin: Schéma du chemin

        Returns:
            Dict avec le code et les métadonnées
        """
        code = self.generate(chemin)
        filename = f"chemin_{chemin.etat_initial}_vers_{chemin.etat_sortie}.py"

        return {
            "filename": filename,
            "code": code,
            "class_name": chemin.nom_classe,
            "output_path": str(self.output_dir / filename),
        }
