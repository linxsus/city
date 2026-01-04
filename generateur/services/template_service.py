"""Service pour la gestion des templates dans le générateur."""

import json
import shutil
from dataclasses import dataclass
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


@dataclass
class DuplicateInfo:
    """Information sur un duplicata détecté."""
    path: str
    similarity: float
    template_name: str
    is_exact: bool


class TemplateService:
    """Service pour la gestion des templates multi-variantes."""

    def __init__(self):
        self.templates_dir = FRAMEWORK_TEMPLATES_DIR
        self._image_service = None
        self._database_service = None

    @property
    def image_service(self):
        """Lazy loading du service d'images."""
        if self._image_service is None:
            from .image_service import get_image_service
            self._image_service = get_image_service()
        return self._image_service

    @property
    def database(self):
        """Lazy loading du service de base de données."""
        if self._database_service is None:
            from .database_service import get_database_service
            self._database_service = get_database_service()
        return self._database_service

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
            # Supprimer les hashes de la base de données
            for variant_file in template_dir.glob("*.png"):
                rel_path = variant_file.relative_to(self.templates_dir)
                self.database.delete_file_version(str(variant_file), str(rel_path))

            shutil.rmtree(template_dir)
            return True
        except OSError:
            return False

    def check_duplicate(
        self,
        image_path: str,
        region: Optional[RegionSchema] = None,
        exact_threshold: float = 0.95,
        similar_threshold: float = 0.85,
    ) -> dict:
        """Vérifie si une image est un duplicata d'un template existant.

        Args:
            image_path: Chemin de l'image à vérifier
            region: Région à extraire (optionnel)
            exact_threshold: Seuil pour duplicata exact (0.95 = 95% similaire)
            similar_threshold: Seuil pour image similaire (0.85 = 85% similaire)

        Returns:
            Dict avec is_duplicate, exact_matches, similar_matches
        """
        try:
            # Charger l'image
            source_image = Image.open(image_path)

            # Extraire la région si spécifiée
            if region:
                source_image = source_image.crop((
                    region.x,
                    region.y,
                    region.x + region.width,
                    region.y + region.height,
                ))

            # Sauvegarder temporairement pour calculer le hash
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                source_image.save(tmp.name)
                temp_path = tmp.name

            # Calculer le hash
            new_hash = self.image_service.compute_dhash(temp_path)

            # Nettoyer le fichier temporaire
            Path(temp_path).unlink()

            # Chercher les duplicatas dans la base de données
            db_matches = self.database.find_templates_by_hash(
                new_hash,
                max_distance=int((1 - similar_threshold) * 64),
            )

            exact_matches = []
            similar_matches = []

            for match in db_matches:
                similarity = 1 - (match.get("distance", 64) / 64)
                match_info = {
                    "path": match["path"],
                    "similarity": round(similarity * 100, 1),
                    "template_name": self._get_template_name_from_path(match["path"]),
                }

                if similarity >= exact_threshold:
                    exact_matches.append(match_info)
                elif similarity >= similar_threshold:
                    similar_matches.append(match_info)

            # Si pas de résultats dans la DB, scanner les fichiers
            if not db_matches:
                file_duplicates = self._scan_files_for_duplicates(
                    new_hash, exact_threshold, similar_threshold
                )
                exact_matches = file_duplicates["exact"]
                similar_matches = file_duplicates["similar"]

            return {
                "is_duplicate": len(exact_matches) > 0,
                "has_similar": len(similar_matches) > 0,
                "exact_matches": exact_matches,
                "similar_matches": similar_matches,
                "hash": new_hash,
            }

        except Exception as e:
            return {
                "is_duplicate": False,
                "has_similar": False,
                "exact_matches": [],
                "similar_matches": [],
                "error": str(e),
            }

    def _scan_files_for_duplicates(
        self,
        target_hash: str,
        exact_threshold: float,
        similar_threshold: float,
    ) -> dict:
        """Scanne les fichiers templates pour trouver des duplicatas.

        Args:
            target_hash: Hash de l'image cible
            exact_threshold: Seuil pour duplicata exact
            similar_threshold: Seuil pour image similaire

        Returns:
            Dict avec exact et similar matches
        """
        exact = []
        similar = []

        for png_file in self.templates_dir.rglob("*.png"):
            try:
                file_hash = self.image_service.compute_dhash(str(png_file))
                distance = self.image_service.hamming_distance(target_hash, file_hash)
                similarity = 1 - (distance / 64)

                if similarity >= similar_threshold:
                    match_info = {
                        "path": str(png_file.relative_to(self.templates_dir)),
                        "similarity": round(similarity * 100, 1),
                        "template_name": self._get_template_name_from_path(str(png_file)),
                    }

                    if similarity >= exact_threshold:
                        exact.append(match_info)
                    else:
                        similar.append(match_info)

                    # Indexer dans la base de données pour les prochaines recherches
                    self.database.save_template_hash(
                        path=str(png_file.relative_to(self.templates_dir)),
                        dhash=file_hash,
                        source="scan",
                    )

            except Exception:
                continue

        return {"exact": exact, "similar": similar}

    def _get_template_name_from_path(self, path: str) -> str:
        """Extrait le nom du template depuis un chemin."""
        parts = Path(path).parts
        if len(parts) >= 2:
            return parts[-2] if parts[-1].endswith(".png") else parts[-1]
        return Path(path).stem

    def add_variant(
        self,
        template_name: str,
        group: str,
        variant_name: str,
        image_path: str,
        region: Optional[RegionSchema] = None,
        threshold: Optional[float] = None,
        force: bool = False,
    ) -> dict:
        """Ajoute une variante à un template.

        Args:
            template_name: Nom du template
            group: Groupe de la variante
            variant_name: Nom du fichier de variante
            image_path: Chemin de l'image source
            region: Région à extraire (optionnel)
            threshold: Seuil spécifique (optionnel)
            force: Forcer l'ajout même si duplicata (défaut: False)

        Returns:
            Dict avec success, path, et éventuellement duplicates
        """
        template_dir = self._find_template_dir(template_name)
        if not template_dir:
            return {"success": False, "error": f"Template '{template_name}' non trouvé"}

        # Vérifier les duplicatas (sauf si force=True)
        if not force:
            dup_check = self.check_duplicate(image_path, region)
            if dup_check.get("is_duplicate"):
                return {
                    "success": False,
                    "error": "Image duplicata détectée",
                    "duplicates": dup_check["exact_matches"],
                    "similar": dup_check.get("similar_matches", []),
                    "requires_force": True,
                }
            elif dup_check.get("has_similar"):
                return {
                    "success": False,
                    "error": "Images similaires détectées",
                    "similar": dup_check["similar_matches"],
                    "requires_force": True,
                }

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

            # Calculer et stocker le hash
            variant_hash = self.image_service.compute_dhash(str(variant_path))
            rel_path = variant_path.relative_to(self.templates_dir)

            # Stocker dans la base de données
            img = Image.open(variant_path)
            self.database.save_template_hash(
                path=str(rel_path),
                dhash=variant_hash,
                width=img.width,
                height=img.height,
                source="generator",
            )

            # Mettre à jour la config
            if "group_configs" not in config:
                config["group_configs"] = {}

            if group not in config["group_configs"]:
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

            return {
                "success": True,
                "path": str(variant_path),
                "hash": variant_hash,
                "message": f"Variante '{variant_name}' ajoutée au template '{template_name}'",
            }

        except (json.JSONDecodeError, IOError, OSError) as e:
            return {"success": False, "error": f"Erreur lors de l'ajout: {e}"}

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

                # Supprimer le hash de la base de données
                rel_path = variant_path.relative_to(self.templates_dir)
                # Note: On pourrait ajouter une méthode delete_template_hash si nécessaire

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

    def index_all_templates(self) -> dict:
        """Indexe tous les templates existants dans la base de données.

        Returns:
            Dict avec le nombre de templates indexés
        """
        indexed = 0
        errors = 0

        for png_file in self.templates_dir.rglob("*.png"):
            try:
                file_hash = self.image_service.compute_dhash(str(png_file))
                img = Image.open(png_file)
                rel_path = png_file.relative_to(self.templates_dir)

                self.database.save_template_hash(
                    path=str(rel_path),
                    dhash=file_hash,
                    width=img.width,
                    height=img.height,
                    source="index",
                )
                indexed += 1

            except Exception:
                errors += 1

        return {
            "indexed": indexed,
            "errors": errors,
            "message": f"{indexed} templates indexés, {errors} erreurs",
        }

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
