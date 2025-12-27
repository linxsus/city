"""Générateur de code pour les actions simples."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from ..config import FRAMEWORK_ACTIONS_SIMPLE_DIR
from ..models.schemas import ActionSchema


class ActionGenerator:
    """Génère le code Python pour les classes Action."""

    def __init__(self):
        templates_dir = Path(__file__).parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(templates_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.template = self.env.get_template("action.py.j2")
        self.output_dir = FRAMEWORK_ACTIONS_SIMPLE_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, action: ActionSchema) -> str:
        """
        Génère le code Python pour une action.

        Args:
            action: Schéma de l'action à générer

        Returns:
            Code Python généré
        """
        # Préparer les paramètres du constructeur
        params_with_defaults = []
        params_super = []
        params_init = []

        for param in action.parametres:
            name = param.get("name", "")
            param_type = param.get("type", "Any")
            default = param.get("default")

            if default is not None:
                if isinstance(default, str):
                    params_with_defaults.append(f'{name}: {param_type} = "{default}"')
                else:
                    params_with_defaults.append(f"{name}: {param_type} = {default}")
            else:
                params_with_defaults.append(f"{name}: {param_type}")

            params_init.append(f"self.{name} = {name}")

        return self.template.render(
            nom_classe=action.nom_classe,
            nom=action.nom,
            description=action.description or "",
            params_with_defaults=params_with_defaults,
            params_init=params_init,
            condition_code=action.condition_code,
            run_code=action.run_code,
            erreurs_verif_apres=action.erreurs_verif_apres,
            erreurs_si_echec=action.erreurs_si_echec,
        )

    def save(self, action: ActionSchema) -> Path:
        """
        Sauvegarde le code généré dans un fichier.

        Args:
            action: Schéma de l'action

        Returns:
            Chemin du fichier créé
        """
        code = self.generate(action)

        filename = f"action_{action.nom}.py"
        filepath = self.output_dir / filename
        filepath.write_text(code, encoding="utf-8")

        action.fichier_genere = str(filepath)

        return filepath

    def preview(self, action: ActionSchema) -> dict:
        """
        Génère une prévisualisation du code.

        Args:
            action: Schéma de l'action

        Returns:
            Dict avec le code et les métadonnées
        """
        code = self.generate(action)
        filename = f"action_{action.nom}.py"

        return {
            "filename": filename,
            "code": code,
            "class_name": action.nom_classe,
            "output_path": str(self.output_dir / filename),
        }
