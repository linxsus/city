"""Service d'import des éléments existants du framework."""

import ast
import re
from pathlib import Path

from ..config import FRAMEWORK_TEMPLATES_DIR
from .parser_service import ClassInfo, get_parser


class ImportedEtat:
    """État importé avec ses métadonnées."""

    def __init__(self, class_info: ClassInfo):
        self.class_info = class_info
        self.nom = class_info.nom
        self.nom_classe = class_info.nom_classe
        self.fichier = class_info.fichier
        self.groupes = class_info.attributs.get("groupes", [])
        self.priorite = class_info.attributs.get("priorite", 0)

        # Analyser le code pour trouver les templates et textes
        parser = get_parser()
        self.templates = parser.find_template_references(class_info.code_source)
        self.textes = parser.find_text_references(class_info.code_source)

        # Déterminer la méthode de vérification
        self.methode_verif = self._detect_methode_verif()

    def _detect_methode_verif(self) -> str:
        """Détecte la méthode de vérification utilisée."""
        has_image = len(self.templates) > 0
        has_text = len(self.textes) > 0

        if has_image and has_text:
            return "combinaison"
        elif has_text:
            return "texte"
        else:
            return "image"

    def to_dict(self) -> dict:
        return {
            "nom": self.nom,
            "nom_classe": self.nom_classe,
            "fichier": self.fichier,
            "groupes": self.groupes,
            "priorite": self.priorite,
            "templates": self.templates,
            "textes": self.textes,
            "methode_verif": self.methode_verif,
            "code_source": self.class_info.code_source,
        }


class ImportedChemin:
    """Chemin importé avec ses métadonnées."""

    def __init__(self, class_info: ClassInfo):
        self.class_info = class_info
        self.nom = class_info.nom
        self.nom_classe = class_info.nom_classe
        self.fichier = class_info.fichier
        self.etat_initial = class_info.attributs.get("etat_initial", "")
        self.etat_sortie = class_info.attributs.get("etat_sortie", "")

        # Analyser les actions
        parser = get_parser()
        self.templates = parser.find_template_references(class_info.code_source)
        self.textes = parser.find_text_references(class_info.code_source)

    def to_dict(self) -> dict:
        return {
            "nom": self.nom,
            "nom_classe": self.nom_classe,
            "fichier": self.fichier,
            "etat_initial": self.etat_initial,
            "etat_sortie": self.etat_sortie,
            "templates": self.templates,
            "textes": self.textes,
            "code_source": self.class_info.code_source,
        }


class ImportedAction:
    """Action importée avec ses métadonnées."""

    def __init__(self, class_info: ClassInfo, action_type: str = "simple"):
        self.class_info = class_info
        self.nom = class_info.nom
        self.nom_classe = class_info.nom_classe
        self.fichier = class_info.fichier
        self.action_type = action_type  # "simple" ou "longue"

        # Analyser le code pour trouver les templates et textes
        parser = get_parser()
        self.templates = parser.find_template_references(class_info.code_source)
        self.textes = parser.find_text_references(class_info.code_source)

    def to_dict(self) -> dict:
        return {
            "nom": self.nom,
            "nom_classe": self.nom_classe,
            "fichier": self.fichier,
            "action_type": self.action_type,
            "templates": self.templates,
            "textes": self.textes,
            "code_source": self.class_info.code_source,
        }


class ImportService:
    """Service pour importer et gérer les éléments existants."""

    def __init__(self):
        self.parser = get_parser()
        self.templates_dir = FRAMEWORK_TEMPLATES_DIR

    def get_all_etats(self) -> list[ImportedEtat]:
        """Récupère tous les états existants."""
        classes = self.parser.parse_etats()
        return [ImportedEtat(c) for c in classes if c.type_classe == "etat"]

    def get_all_chemins(self) -> list[ImportedChemin]:
        """Récupère tous les chemins existants."""
        classes = self.parser.parse_chemins()
        return [ImportedChemin(c) for c in classes if c.type_classe == "chemin"]

    def get_etat_by_name(self, nom: str) -> ImportedEtat | None:
        """Récupère un état par son nom."""
        etats = self.get_all_etats()
        for etat in etats:
            if etat.nom == nom:
                return etat
        return None

    def get_chemin_by_name(self, nom: str) -> ImportedChemin | None:
        """Récupère un chemin par son nom."""
        chemins = self.get_all_chemins()
        for chemin in chemins:
            if chemin.nom == nom:
                return chemin
        return None

    def get_all_actions(self) -> list[ImportedAction]:
        """Récupère toutes les actions (simples et longues)."""
        actions = []

        # Actions simples
        classes_simples = self.parser.parse_actions_simples()
        for c in classes_simples:
            if c.type_classe == "action":
                actions.append(ImportedAction(c, "simple"))

        # Actions longues
        classes_longues = self.parser.parse_actions_longues()
        for c in classes_longues:
            if c.type_classe == "action":
                actions.append(ImportedAction(c, "longue"))

        return actions

    def get_action_by_name(self, nom: str) -> ImportedAction | None:
        """Récupère une action par son nom."""
        actions = self.get_all_actions()
        for action in actions:
            if action.nom == nom:
                return action
        return None

    def _normalize_path(self, path: str) -> str:
        """Normalise un chemin en utilisant des forward slashes."""
        return path.replace("\\", "/")

    def get_all_templates(self) -> list[dict]:
        """Liste tous les templates existants."""
        templates = []

        if not self.templates_dir.exists():
            return templates

        for filepath in self.templates_dir.rglob("*.png"):
            rel_path = filepath.relative_to(self.templates_dir)
            # Normaliser les chemins avec des forward slashes
            normalized_path = self._normalize_path(str(rel_path))
            folder = str(rel_path.parent)
            normalized_folder = self._normalize_path(folder) if folder != "." else None

            templates.append({
                "path": normalized_path,
                "full_path": str(filepath),
                "name": filepath.stem,
                "folder": normalized_folder,
                "size": filepath.stat().st_size,
            })

        return templates

    def get_template_usage(self, template_path: str) -> dict:
        """
        Trouve où un template est utilisé.

        Args:
            template_path: Chemin relatif du template

        Returns:
            Dict avec les états et chemins qui l'utilisent
        """
        usage = {
            "etats": [],
            "chemins": [],
        }

        # Normaliser le chemin recherché
        normalized_search = self._normalize_path(template_path)

        # Chercher dans les états
        for etat in self.get_all_etats():
            normalized_templates = [self._normalize_path(t) for t in etat.templates]
            if normalized_search in normalized_templates:
                usage["etats"].append(etat.nom)

        # Chercher dans les chemins
        for chemin in self.get_all_chemins():
            normalized_templates = [self._normalize_path(t) for t in chemin.templates]
            if normalized_search in normalized_templates:
                usage["chemins"].append(chemin.nom)

        return usage

    def get_summary(self) -> dict:
        """Retourne un résumé des éléments existants."""
        etats = self.get_all_etats()
        chemins = self.get_all_chemins()
        actions = self.get_all_actions()
        templates = self.get_all_templates()

        # Collecter les groupes uniques
        all_groups = set()
        for etat in etats:
            all_groups.update(etat.groupes)

        return {
            "etats": {
                "count": len(etats),
                "items": [e.to_dict() for e in etats],
            },
            "chemins": {
                "count": len(chemins),
                "items": [c.to_dict() for c in chemins],
            },
            "actions": {
                "count": len(actions),
                "items": [a.to_dict() for a in actions],
            },
            "templates": {
                "count": len(templates),
                "items": templates,
            },
            "groupes": sorted(all_groups),
        }

    def find_orphan_templates(self) -> list[dict]:
        """Trouve les templates qui ne sont utilisés nulle part."""
        templates = self.get_all_templates()
        orphans = []

        for template in templates:
            usage = self.get_template_usage(template["path"])
            if not usage["etats"] and not usage["chemins"]:
                orphans.append(template)

        return orphans

    def find_missing_templates(self) -> list[dict]:
        """Trouve les templates référencés mais inexistants."""
        missing = []
        # Normaliser tous les chemins existants
        existing_paths = {t["path"] for t in self.get_all_templates()}

        # Pour éviter les doublons
        seen = set()

        # Vérifier les états
        for etat in self.get_all_etats():
            for template in etat.templates:
                normalized = self._normalize_path(template)
                if normalized not in existing_paths and normalized not in seen:
                    seen.add(normalized)
                    missing.append({
                        "template": template,
                        "used_in": etat.nom,
                        "type": "etat",
                    })

        # Vérifier les chemins
        for chemin in self.get_all_chemins():
            for template in chemin.templates:
                normalized = self._normalize_path(template)
                if normalized not in existing_paths and normalized not in seen:
                    seen.add(normalized)
                    missing.append({
                        "template": template,
                        "used_in": chemin.nom,
                        "type": "chemin",
                    })

        return missing

    def _update_class_attribute(
        self,
        filepath: Path,
        class_name: str,
        attr_name: str,
        new_value: any,
    ) -> bool:
        """
        Met à jour un attribut de classe dans un fichier Python.

        Args:
            filepath: Chemin du fichier
            class_name: Nom de la classe à modifier
            attr_name: Nom de l'attribut à modifier
            new_value: Nouvelle valeur de l'attribut

        Returns:
            True si succès, False sinon
        """
        if not filepath.exists():
            return False

        try:
            code = filepath.read_text(encoding="utf-8")
            lines = code.split("\n")

            # Parser le fichier pour trouver la classe
            tree = ast.parse(code)
            class_node = None

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == class_name:
                    class_node = node
                    break

            if not class_node:
                return False

            # Trouver l'attribut dans la classe
            attr_line = None
            for item in class_node.body:
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name) and target.id == attr_name:
                            attr_line = item.lineno - 1
                            break

            if attr_line is None:
                # L'attribut n'existe pas, l'ajouter après la ligne class
                insert_line = class_node.lineno
                # Trouver l'indentation
                class_line = lines[class_node.lineno - 1]
                indent = len(class_line) - len(class_line.lstrip()) + 4
                new_attr_line = " " * indent + f"{attr_name} = {repr(new_value)}"
                lines.insert(insert_line, new_attr_line)
            else:
                # Remplacer la ligne existante
                old_line = lines[attr_line]
                indent = len(old_line) - len(old_line.lstrip())
                lines[attr_line] = " " * indent + f"{attr_name} = {repr(new_value)}"

            # Écrire le fichier
            filepath.write_text("\n".join(lines), encoding="utf-8")
            return True

        except Exception as e:
            print(f"Erreur lors de la mise à jour: {e}")
            return False

    def update_etat(
        self,
        nom: str,
        groupes: list[str] | None = None,
        priorite: int | None = None,
    ) -> dict:
        """
        Met à jour un état existant.

        Args:
            nom: Nom de l'état à modifier
            groupes: Nouveaux groupes (optionnel)
            priorite: Nouvelle priorité (optionnel)

        Returns:
            Dict avec succès/erreur
        """
        etat = self.get_etat_by_name(nom)
        if not etat:
            return {"success": False, "error": f"État '{nom}' non trouvé"}

        filepath = Path(etat.fichier)
        class_name = etat.nom_classe
        updated = []
        errors = []

        if groupes is not None:
            if self._update_class_attribute(filepath, class_name, "groupes", groupes):
                updated.append("groupes")
            else:
                errors.append("groupes")

        if priorite is not None:
            if self._update_class_attribute(filepath, class_name, "priorite", priorite):
                updated.append("priorite")
            else:
                errors.append("priorite")

        if errors:
            return {
                "success": False,
                "error": f"Échec de mise à jour: {', '.join(errors)}",
                "updated": updated,
            }

        return {
            "success": True,
            "message": f"Attributs mis à jour: {', '.join(updated)}",
            "updated": updated,
        }

    def update_chemin(
        self,
        nom: str,
        etat_initial: str | None = None,
        etat_sortie: str | None = None,
    ) -> dict:
        """
        Met à jour un chemin existant.

        Args:
            nom: Nom du chemin à modifier
            etat_initial: Nouvel état initial (optionnel)
            etat_sortie: Nouvel état de sortie (optionnel)

        Returns:
            Dict avec succès/erreur
        """
        chemin = self.get_chemin_by_name(nom)
        if not chemin:
            return {"success": False, "error": f"Chemin '{nom}' non trouvé"}

        filepath = Path(chemin.fichier)
        class_name = chemin.nom_classe
        updated = []
        errors = []

        if etat_initial is not None:
            if self._update_class_attribute(filepath, class_name, "etat_initial", etat_initial):
                updated.append("etat_initial")
            else:
                errors.append("etat_initial")

        if etat_sortie is not None:
            if self._update_class_attribute(filepath, class_name, "etat_sortie", etat_sortie):
                updated.append("etat_sortie")
            else:
                errors.append("etat_sortie")

        if errors:
            return {
                "success": False,
                "error": f"Échec de mise à jour: {', '.join(errors)}",
                "updated": updated,
            }

        return {
            "success": True,
            "message": f"Attributs mis à jour: {', '.join(updated)}",
            "updated": updated,
        }


# Singleton
_import_service: ImportService | None = None


def get_import_service() -> ImportService:
    """Retourne l'instance singleton du service d'import."""
    global _import_service
    if _import_service is None:
        _import_service = ImportService()
    return _import_service
