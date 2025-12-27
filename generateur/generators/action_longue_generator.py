"""Générateur de code pour les actions longues."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from ..config import FRAMEWORK_ACTIONS_LONGUE_DIR
from ..models.schemas import ActionLongueSchema, ActionReference, ControlBlock


class ActionLongueGenerator:
    """Génère le code Python pour les classes ActionLongue."""

    def __init__(self):
        templates_dir = Path(__file__).parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(templates_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.template = self.env.get_template("action_longue.py.j2")
        self.output_dir = FRAMEWORK_ACTIONS_LONGUE_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _get_imports(self, blocks: list) -> set[str]:
        """Détermine les imports nécessaires."""
        imports = set()

        for block in blocks:
            if isinstance(block, ActionReference) or (isinstance(block, dict) and block.get("type") in ["ActionBouton", "ActionAttendre", "ActionTexte"]):
                block_type = block.type if isinstance(block, ActionReference) else block.get("type")
                if block_type == "ActionBouton":
                    imports.add("from actions.simple.action_bouton import ActionBouton")
                elif block_type == "ActionAttendre":
                    imports.add("from actions.simple.action_attendre import ActionAttendre")
                elif block_type == "ActionTexte":
                    imports.add("from actions.simple.action_texte import ActionTexte")
            elif isinstance(block, ControlBlock) or (isinstance(block, dict) and block.get("type") in ["if", "if_else", "while", "for"]):
                block_type = block.type if isinstance(block, ControlBlock) else block.get("type")
                if block_type in ["if", "if_else"]:
                    if block_type == "if":
                        imports.add("from actions.boucle.action_if import ActionIf")
                    else:
                        imports.add("from actions.boucle.action_if import ActionIfElse")
                elif block_type == "while":
                    imports.add("from actions.boucle.action_loops import ActionWhile")
                elif block_type == "for":
                    imports.add("from actions.boucle.action_loops import ActionFor")

                # Récursif pour les actions internes
                actions = block.actions if isinstance(block, ControlBlock) else block.get("actions", [])
                imports.update(self._get_imports(actions))

                actions_else = block.actions_else if isinstance(block, ControlBlock) else block.get("actions_else", [])
                if actions_else:
                    imports.update(self._get_imports(actions_else))

        return imports

    def _generate_block_code(self, block, indent_level: int = 0) -> str:
        """Génère le code pour un bloc."""
        indent = "    " * indent_level

        if isinstance(block, ActionReference) or (isinstance(block, dict) and block.get("type") in ["ActionBouton", "ActionAttendre", "ActionTexte"]):
            return self._generate_action_code(block, indent_level)

        block_type = block.type if isinstance(block, ControlBlock) else block.get("type")
        condition = block.condition if isinstance(block, ControlBlock) else block.get("condition")
        actions = block.actions if isinstance(block, ControlBlock) else block.get("actions", [])
        actions_else = block.actions_else if isinstance(block, ControlBlock) else block.get("actions_else", [])
        iterations = block.iterations if isinstance(block, ControlBlock) else block.get("iterations")
        max_iterations = block.max_iterations if isinstance(block, ControlBlock) else block.get("max_iterations", 100)

        if block_type == "if":
            actions_code = ",\n".join(
                self._generate_block_code(a, indent_level + 2) for a in actions
            )
            return f"""{indent}ActionIf(
{indent}    fenetre,
{indent}    condition_func={condition},
{indent}    actions_si_vrai=[
{actions_code}
{indent}    ]
{indent})"""

        elif block_type == "if_else":
            actions_vrai = ",\n".join(
                self._generate_block_code(a, indent_level + 2) for a in actions
            )
            actions_faux = ",\n".join(
                self._generate_block_code(a, indent_level + 2) for a in actions_else
            )
            return f"""{indent}ActionIfElse(
{indent}    fenetre,
{indent}    condition_func={condition},
{indent}    actions_si_vrai=[
{actions_vrai}
{indent}    ],
{indent}    actions_si_faux=[
{actions_faux}
{indent}    ]
{indent})"""

        elif block_type == "while":
            actions_code = ",\n".join(
                self._generate_block_code(a, indent_level + 2) for a in actions
            )
            return f"""{indent}ActionWhile(
{indent}    fenetre,
{indent}    condition_func={condition},
{indent}    actions=[
{actions_code}
{indent}    ],
{indent}    max_iterations={max_iterations}
{indent})"""

        elif block_type == "for":
            actions_code = ",\n".join(
                self._generate_block_code(a, indent_level + 2) for a in actions
            )
            return f"""{indent}ActionFor(
{indent}    fenetre,
{indent}    nombre_iterations={iterations},
{indent}    actions=[
{actions_code}
{indent}    ]
{indent})"""

        return f"{indent}# Bloc inconnu: {block_type}"

    def _generate_action_code(self, action, indent_level: int = 0) -> str:
        """Génère le code pour une action simple."""
        indent = "    " * indent_level

        if isinstance(action, ActionReference):
            action_type = action.type
            params = action.parametres
        else:
            action_type = action.get("type")
            params = action.get("parametres", {})

        if action_type == "ActionBouton":
            template_path = params.get("template_path", "")
            threshold = params.get("threshold", 0.8)
            offset_x = params.get("offset_x", 0)
            offset_y = params.get("offset_y", 0)

            if offset_x or offset_y:
                return f'{indent}ActionBouton(fenetre, "{template_path}", threshold={threshold}, offset=({offset_x}, {offset_y}))'
            return f'{indent}ActionBouton(fenetre, "{template_path}", threshold={threshold})'

        elif action_type == "ActionAttendre":
            duree = params.get("duree", 1)
            return f"{indent}ActionAttendre(fenetre, {duree})"

        elif action_type == "ActionTexte":
            texte = params.get("texte_recherche", "")
            offset_x = params.get("offset_x", 0)
            offset_y = params.get("offset_y", 0)

            if offset_x or offset_y:
                return f'{indent}ActionTexte(fenetre, "{texte}", offset=({offset_x}, {offset_y}))'
            return f'{indent}ActionTexte(fenetre, "{texte}")'

        return f"{indent}# Action non supportée: {action_type}"

    def generate(self, action_longue: ActionLongueSchema) -> str:
        """
        Génère le code Python pour une action longue.

        Args:
            action_longue: Schéma de l'action longue

        Returns:
            Code Python généré
        """
        imports = sorted(self._get_imports(action_longue.blocks))

        # Générer le code des blocs
        blocks_code = []
        for block in action_longue.blocks:
            blocks_code.append(self._generate_block_code(block, indent_level=3))

        return self.template.render(
            nom_classe=action_longue.nom_classe,
            nom=action_longue.nom,
            description=action_longue.description or "",
            imports=imports,
            blocks_code=",\n".join(blocks_code),
            etat_requis=action_longue.etat_requis,
            maintenant=action_longue.maintenant,
        )

    def save(self, action_longue: ActionLongueSchema) -> Path:
        """
        Sauvegarde le code généré dans un fichier.

        Args:
            action_longue: Schéma de l'action longue

        Returns:
            Chemin du fichier créé
        """
        code = self.generate(action_longue)

        filename = f"action_{action_longue.nom}.py"
        filepath = self.output_dir / filename
        filepath.write_text(code, encoding="utf-8")

        action_longue.fichier_genere = str(filepath)

        return filepath

    def preview(self, action_longue: ActionLongueSchema) -> dict:
        """
        Génère une prévisualisation du code.

        Args:
            action_longue: Schéma de l'action longue

        Returns:
            Dict avec le code et les métadonnées
        """
        code = self.generate(action_longue)
        filename = f"action_{action_longue.nom}.py"

        return {
            "filename": filename,
            "code": code,
            "class_name": action_longue.nom_classe,
            "output_path": str(self.output_dir / filename),
        }
