"""Parser Python pour extraire les classes existantes du framework."""

import ast
import re
from pathlib import Path
from typing import Any

from ..config import (
    FRAMEWORK_ACTIONS_LONGUE_DIR,
    FRAMEWORK_ACTIONS_SIMPLE_DIR,
    FRAMEWORK_CHEMINS_DIR,
    FRAMEWORK_ETATS_DIR,
)


class ClassInfo:
    """Informations extraites d'une classe."""

    def __init__(
        self,
        nom: str,
        nom_classe: str,
        fichier: str,
        type_classe: str,
        attributs: dict[str, Any],
        code_source: str,
    ):
        self.nom = nom
        self.nom_classe = nom_classe
        self.fichier = fichier
        self.type_classe = type_classe
        self.attributs = attributs
        self.code_source = code_source

    def to_dict(self) -> dict:
        return {
            "nom": self.nom,
            "nom_classe": self.nom_classe,
            "fichier": self.fichier,
            "type_classe": self.type_classe,
            "attributs": self.attributs,
        }


class PythonParser:
    """Parser pour extraire les informations des classes Python."""

    def __init__(self):
        self.etats_dir = FRAMEWORK_ETATS_DIR
        self.chemins_dir = FRAMEWORK_CHEMINS_DIR
        self.actions_simple_dir = FRAMEWORK_ACTIONS_SIMPLE_DIR
        self.actions_longue_dir = FRAMEWORK_ACTIONS_LONGUE_DIR

    def parse_file(self, filepath: Path) -> list[ClassInfo]:
        """
        Parse un fichier Python et extrait les informations des classes.

        Args:
            filepath: Chemin du fichier à parser

        Returns:
            Liste des ClassInfo trouvées
        """
        if not filepath.exists():
            return []

        try:
            code = filepath.read_text(encoding="utf-8")
            tree = ast.parse(code)
        except (SyntaxError, UnicodeDecodeError):
            return []

        classes = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_info = self._extract_class_info(node, filepath, code)
                if class_info:
                    classes.append(class_info)

        return classes

    def _extract_class_info(
        self,
        node: ast.ClassDef,
        filepath: Path,
        code: str,
    ) -> ClassInfo | None:
        """Extrait les informations d'une classe AST."""
        # Déterminer le type de classe basé sur l'héritage
        type_classe = self._get_class_type(node)
        if not type_classe:
            return None

        attributs = {}

        # Extraire les attributs de classe
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        attr_name = target.id
                        attr_value = self._get_literal_value(item.value)
                        if attr_value is not None:
                            attributs[attr_name] = attr_value

        # Extraire le nom depuis l'attribut 'nom'
        nom = attributs.get("nom", node.name)

        # Extraire le code source de la classe
        try:
            lines = code.split("\n")
            start_line = node.lineno - 1
            end_line = node.end_lineno if hasattr(node, "end_lineno") else start_line + 20
            code_source = "\n".join(lines[start_line:end_line])
        except Exception:
            code_source = ""

        return ClassInfo(
            nom=nom,
            nom_classe=node.name,
            fichier=str(filepath),
            type_classe=type_classe,
            attributs=attributs,
            code_source=code_source,
        )

    def _get_class_type(self, node: ast.ClassDef) -> str | None:
        """Détermine le type de classe basé sur l'héritage."""
        for base in node.bases:
            base_name = self._get_base_name(base)
            if base_name in ("Etat", "Popup"):
                return "etat"
            elif base_name == "Chemin":
                return "chemin"
            elif base_name in ("Action", "ActionLongue"):
                return "action"
        return None

    def _get_base_name(self, base: ast.expr) -> str:
        """Récupère le nom de la classe de base."""
        if isinstance(base, ast.Name):
            return base.id
        elif isinstance(base, ast.Attribute):
            return base.attr
        return ""

    def _get_literal_value(self, node: ast.expr) -> Any:
        """Extrait la valeur littérale d'un noeud AST."""
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.List):
            return [self._get_literal_value(elt) for elt in node.elts]
        elif isinstance(node, ast.Tuple):
            return tuple(self._get_literal_value(elt) for elt in node.elts)
        elif isinstance(node, ast.Dict):
            return {
                self._get_literal_value(k): self._get_literal_value(v)
                for k, v in zip(node.keys, node.values)
                if k is not None
            }
        elif isinstance(node, ast.Name):
            # Pour les références comme EtatInconnu
            return f"<{node.id}>"
        elif isinstance(node, ast.Call):
            # Pour les appels comme EtatInconnu(...)
            func_name = self._get_base_name(node.func) if hasattr(node, "func") else "Call"
            return f"<{func_name}(...)>"
        return None

    def parse_etats(self) -> list[ClassInfo]:
        """Parse tous les fichiers d'états."""
        etats = []

        if not self.etats_dir.exists():
            return etats

        for filepath in self.etats_dir.glob("*.py"):
            if filepath.name.startswith("__"):
                continue
            etats.extend(self.parse_file(filepath))

        return etats

    def parse_chemins(self) -> list[ClassInfo]:
        """Parse tous les fichiers de chemins."""
        chemins = []

        if not self.chemins_dir.exists():
            return chemins

        for filepath in self.chemins_dir.glob("*.py"):
            if filepath.name.startswith("__"):
                continue
            chemins.extend(self.parse_file(filepath))

        return chemins

    def parse_actions_simples(self) -> list[ClassInfo]:
        """Parse tous les fichiers d'actions simples."""
        actions = []

        if not self.actions_simple_dir.exists():
            return actions

        for filepath in self.actions_simple_dir.glob("*.py"):
            if filepath.name.startswith("__"):
                continue
            actions.extend(self.parse_file(filepath))

        return actions

    def parse_actions_longues(self) -> list[ClassInfo]:
        """Parse tous les fichiers d'actions longues."""
        actions = []

        if not self.actions_longue_dir.exists():
            return actions

        for filepath in self.actions_longue_dir.glob("*.py"):
            if filepath.name.startswith("__"):
                continue
            actions.extend(self.parse_file(filepath))

        return actions

    def parse_all(self) -> dict[str, list[ClassInfo]]:
        """Parse tous les éléments du framework."""
        return {
            "etats": self.parse_etats(),
            "chemins": self.parse_chemins(),
            "actions_simples": self.parse_actions_simples(),
            "actions_longues": self.parse_actions_longues(),
        }

    def find_template_references(self, code: str) -> list[str]:
        """
        Trouve les références aux templates dans le code.

        Args:
            code: Code source à analyser

        Returns:
            Liste des chemins de templates trouvés
        """
        templates = []

        # Pattern pour detect_image("template.png") ou similaire
        patterns = [
            r'detect_image\s*\(\s*["\']([^"\']+)["\']',
            r'find_image\s*\(\s*["\']([^"\']+)["\']',
            r'ActionBouton\s*\([^,]+,\s*["\']([^"\']+)["\']',
            r'template_path\s*=\s*["\']([^"\']+)["\']',
            r'image_detection\s*=\s*["\']([^"\']+)["\']',
            r'image_fermeture\s*=\s*["\']([^"\']+)["\']',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, code)
            templates.extend(matches)

        return list(set(templates))

    def find_text_references(self, code: str) -> list[str]:
        """
        Trouve les références aux textes OCR dans le code.

        Args:
            code: Code source à analyser

        Returns:
            Liste des textes trouvés
        """
        texts = []

        patterns = [
            r'detect_text\s*\(\s*["\']([^"\']+)["\']',
            r'find_text\s*\(\s*["\']([^"\']+)["\']',
            r'ActionTexte\s*\([^,]+,\s*["\']([^"\']+)["\']',
            r'texte_ocr\s*=\s*["\']([^"\']+)["\']',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, code)
            texts.extend(matches)

        return list(set(texts))


# Singleton
_parser: PythonParser | None = None


def get_parser() -> PythonParser:
    """Retourne l'instance singleton du parser."""
    global _parser
    if _parser is None:
        _parser = PythonParser()
    return _parser
