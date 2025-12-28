"""Service pour la gestion des templates dans le générateur."""

import json
import shutil
from pathlib import Path
from typing import Optional

from PIL import Image

from ..config import FRAMEWORK_TEMPLATES_DIR
from ..models.schemas import (
    GroupConfigSchema,
    RegionSchema,
    TemplateConfigCreate,
    TemplateListItem,
)


class TemplateService:
    """Service pour la gestion des templates multi-variantes."""

    def __init__(self):
        self.templates_dir = FRAMEWORK_TEMPLATES_DIR

    def list_templates(self, category: Optional[str] = None) -> list[TemplateListItem]:
        """Liste tous les templates disponibles.

        Args:
            category: Filtrer par catégorie (optionnel)

        Returns:
            Liste des templates
        """
        templates = []

        for category_dir in self.templates_dir.iterdir():
            if not category_dir.is_dir():
                continue

            if category and category_dir.name != category:
                continue

            for template_dir in category_dir.iterdir():
                config_file = template_dir / "config.json"
                if not template_dir.is_dir() or not config_file.exists():
                    continue

                try:
                    with open(config_file, encoding="utf-8") as f:
                        config = json.load(f)

                    # Compter les variantes
                    variant_count = sum(
                        len(gc.get("variants", []))
                        for gc in config.get("group_configs", {}).values()
                    )

                    templates.append(TemplateListItem(
                        name=config.get("name", template_dir.name),
                        category=category_dir.name,
                        description=config.get("description", ""),
                        groups=list(config.get("group_configs", {}).keys()),
                        variant_count=variant_count,
                    ))
                except (json.JSONDecodeError, IOError):
                    continue

        return sorted(templates, key=lambda t: (t.category, t.name))

    def list_categories(self) -> list[str]:
        """Liste toutes les catégories de templates.

        Returns:
            Liste des noms de catégories
        """
        categories = set()

        for category_dir in self.templates_dir.iterdir():
            if not category_dir.is_dir():
                continue

            # Vérifier qu'il y a au moins un template valide
            for template_dir in category_dir.iterdir():
                if template_dir.is_dir() and (template_dir / "config.json").exists():
                    categories.add(category_dir.name)
                    break

        return sorted(categories)

    def list_groups(self) -> list[str]:
        """Liste tous les groupes utilisés dans les templates.

        Returns:
            Liste des noms de groupes
        """
        groups = set()

        for template in self.list_templates():
            groups.update(template.groups)

        return sorted(groups)

    def get_template(self, template_name: str) -> Optional[dict]:
        """Récupère la configuration d'un template.

        Args:
            template_name: Nom du template

        Returns:
            Configuration du template ou None
        """
        template_dir = self._find_template_dir(template_name)
        if not template_dir:
            return None

        config_file = template_dir / "config.json"
        try:
            with open(config_file, encoding="utf-8") as f:
                config = json.load(f)
                config["base_path"] = str(template_dir)
                config["category"] = template_dir.parent.name
                return config
        except (json.JSONDecodeError, IOError):
            return None

    def create_template(self, data: TemplateConfigCreate) -> Path:
        """Crée un nouveau template.

        Args:
            data: Données du template

        Returns:
            Chemin vers le dossier du template

        Raises:
            ValueError: Si le template existe déjà
        """
        # Vérifier que la catégorie existe ou la créer
        category_dir = self.templates_dir / data.category
        category_dir.mkdir(parents=True, exist_ok=True)

        # Vérifier que le template n'existe pas déjà
        template_dir = category_dir / data.name
        if template_dir.exists():
            raise ValueError(f"Le template '{data.name}' existe déjà")

        # Créer le dossier
        template_dir.mkdir()

        # Créer le config.json
        config = {
            "name": data.name,
            "description": data.description,
            "group_configs": {
                group: {
                    "variants": gc.variants,
                    "threshold": gc.threshold,
                }
                for group, gc in data.group_configs.items()
            },
        }

        config_file = template_dir / "config.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        return template_dir

    def update_template(self, template_name: str, data: dict) -> bool:
        """Met à jour la configuration d'un template.

        Args:
            template_name: Nom du template
            data: Nouvelles données (partielles)

        Returns:
            True si mis à jour
        """
        template_dir = self._find_template_dir(template_name)
        if not template_dir:
            return False

        config_file = template_dir / "config.json"

        try:
            with open(config_file, encoding="utf-8") as f:
                config = json.load(f)

            # Mettre à jour les champs fournis
            if "description" in data:
                config["description"] = data["description"]
            if "group_configs" in data:
                config["group_configs"] = data["group_configs"]

            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            return True
        except (json.JSONDecodeError, IOError):
            return False

    def delete_template(self, template_name: str) -> bool:
        """Supprime un template et toutes ses variantes.

        Args:
            template_name: Nom du template

        Returns:
            True si supprimé
        """
        template_dir = self._find_template_dir(template_name)
        if not template_dir:
            return False

        try:
            shutil.rmtree(template_dir)
            return True
        except OSError:
            return False

    def add_variant(
        self,
        template_name: str,
        group: str,
        variant_name: str,
        image_path: str,
        region: Optional[RegionSchema] = None,
        threshold: Optional[float] = None,
    ) -> Optional[Path]:
        """Ajoute une variante à un template.

        Args:
            template_name: Nom du template
            group: Groupe de la variante
            variant_name: Nom du fichier de variante
            image_path: Chemin de l'image source
            region: Région à extraire (optionnel)
            threshold: Seuil spécifique (optionnel)

        Returns:
            Chemin de la variante créée ou None
        """
        template_dir = self._find_template_dir(template_name)
        if not template_dir:
            return None

        config_file = template_dir / "config.json"

        try:
            # Charger la config
            with open(config_file, encoding="utf-8") as f:
                config = json.load(f)

            # Charger l'image source
            source_image = Image.open(image_path)

            # Extraire la région si spécifiée
            if region:
                source_image = source_image.crop((
                    region.x,
                    region.y,
                    region.x + region.width,
                    region.y + region.height,
                ))

            # Assurer l'extension .png
            if not variant_name.endswith(".png"):
                variant_name += ".png"

            # Sauvegarder la variante
            variant_path = template_dir / variant_name
            source_image.save(variant_path)

            # Mettre à jour la config
            if group not in config.get("group_configs", {}):
                config["group_configs"][group] = {
                    "variants": [],
                    "threshold": threshold or 0.8,
                }

            if variant_name not in config["group_configs"][group]["variants"]:
                config["group_configs"][group]["variants"].append(variant_name)

            if threshold is not None:
                config["group_configs"][group]["threshold"] = threshold

            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            return variant_path

        except (json.JSONDecodeError, IOError, OSError) as e:
            raise ValueError(f"Erreur lors de l'ajout de la variante: {e}")

    def delete_variant(
        self,
        template_name: str,
        group: str,
        variant_name: str,
    ) -> bool:
        """Supprime une variante d'un template.

        Args:
            template_name: Nom du template
            group: Groupe de la variante
            variant_name: Nom du fichier de variante

        Returns:
            True si supprimée
        """
        template_dir = self._find_template_dir(template_name)
        if not template_dir:
            return False

        config_file = template_dir / "config.json"

        try:
            # Charger la config
            with open(config_file, encoding="utf-8") as f:
                config = json.load(f)

            # Vérifier que le groupe et la variante existent
            if group not in config.get("group_configs", {}):
                return False

            variants = config["group_configs"][group].get("variants", [])
            if variant_name not in variants:
                return False

            # Supprimer le fichier
            variant_path = template_dir / variant_name
            if variant_path.exists():
                variant_path.unlink()

            # Mettre à jour la config
            variants.remove(variant_name)
            config["group_configs"][group]["variants"] = variants

            # Supprimer le groupe s'il n'a plus de variantes
            if not variants:
                del config["group_configs"][group]

            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            return True

        except (json.JSONDecodeError, IOError, OSError):
            return False

    def get_variant_path(self, template_name: str, variant_name: str) -> Optional[Path]:
        """Retourne le chemin d'une variante.

        Args:
            template_name: Nom du template
            variant_name: Nom de la variante

        Returns:
            Chemin de la variante ou None
        """
        template_dir = self._find_template_dir(template_name)
        if not template_dir:
            return None

        variant_path = template_dir / variant_name
        if variant_path.exists():
            return variant_path

        return None

    def _find_template_dir(self, template_name: str) -> Optional[Path]:
        """Trouve le dossier d'un template.

        Args:
            template_name: Nom du template

        Returns:
            Chemin du dossier ou None
        """
        for category_dir in self.templates_dir.iterdir():
            if not category_dir.is_dir():
                continue

            template_dir = category_dir / template_name
            if template_dir.is_dir() and (template_dir / "config.json").exists():
                return template_dir

        return None


# Singleton
_template_service_instance = None


def get_template_service() -> TemplateService:
    """Retourne l'instance singleton du service.

    Returns:
        TemplateService: Instance partagée
    """
    global _template_service_instance
    if _template_service_instance is None:
        _template_service_instance = TemplateService()
    return _template_service_instance
