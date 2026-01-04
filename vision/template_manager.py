"""Gestionnaire de templates avec support multi-variantes et groupes

Ce module gère :
- Le chargement des configurations de templates (config.json)
- La résolution des variantes selon les groupes du manoir
- La recherche de templates avec priorisation dynamique
- La mise à jour des statistiques par manoir

Structure des templates :
    templates/
    └── boutons/
        └── bouton_ok/
            ├── config.json
            ├── v1.png
            └── v2.png

Format config.json :
    {
        "name": "bouton_ok",
        "description": "Bouton OK des popups",
        "group_configs": {
            "bluestack": {
                "variants": ["v1.png", "v2.png"],
                "threshold": 0.8
            },
            "scrcpy": {
                "variants": ["v3.png", "v4.png"],
                "threshold": 0.7
            }
        }
    }
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from utils.config import DATA_DIR, TEMPLATES_DIR
from utils.logger import get_module_logger

if TYPE_CHECKING:
    from manoirs.manoir_base import ManoirBase

logger = get_module_logger("TemplateManager")


@dataclass
class VariantConfig:
    """Configuration d'une variante de template"""
    filename: str
    threshold: float
    group: str  # Groupe d'origine de cette variante
    full_path: Path = field(default=None)


@dataclass
class TemplateConfig:
    """Configuration complète d'un template"""
    name: str
    description: str
    category: str  # Déduit du dossier parent
    base_path: Path  # Chemin vers le dossier du template
    group_configs: Dict[str, dict] = field(default_factory=dict)

    def get_variants_for_groups(self, manoir_groups: List[str]) -> List[VariantConfig]:
        """Retourne les variantes cumulées pour une liste de groupes

        Args:
            manoir_groups: Liste des groupes du manoir (ordre: plus spécifique en premier)

        Returns:
            Liste de VariantConfig cumulées de tous les groupes trouvés
        """
        variants = []
        seen_filenames = set()

        # Parcourir les groupes du manoir (du plus spécifique au plus général)
        for group in manoir_groups:
            if group in self.group_configs:
                config = self.group_configs[group]
                threshold = config.get("threshold", 0.8)

                for filename in config.get("variants", []):
                    # Éviter les doublons si une variante est dans plusieurs groupes
                    if filename not in seen_filenames:
                        seen_filenames.add(filename)
                        variants.append(VariantConfig(
                            filename=filename,
                            threshold=threshold,
                            group=group,
                            full_path=self.base_path / filename
                        ))

        return variants


class TemplateStatsManager:
    """Gère les statistiques de templates par manoir"""

    def __init__(self):
        self._stats_cache: Dict[str, dict] = {}

    def _get_stats_file(self, manoir_id: str) -> Path:
        """Retourne le chemin du fichier de stats pour un manoir"""
        manoir_dir = DATA_DIR / manoir_id
        manoir_dir.mkdir(parents=True, exist_ok=True)
        return manoir_dir / "template_stats.json"

    def load_stats(self, manoir_id: str) -> dict:
        """Charge les stats d'un manoir depuis le fichier"""
        if manoir_id in self._stats_cache:
            return self._stats_cache[manoir_id]

        stats_file = self._get_stats_file(manoir_id)

        if stats_file.exists():
            try:
                with open(stats_file, encoding="utf-8") as f:
                    stats = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Erreur lecture stats {manoir_id}: {e}")
                stats = {}
        else:
            stats = {}

        self._stats_cache[manoir_id] = stats
        return stats

    def save_stats(self, manoir_id: str):
        """Sauvegarde les stats d'un manoir"""
        if manoir_id not in self._stats_cache:
            return

        stats_file = self._get_stats_file(manoir_id)

        try:
            with open(stats_file, "w", encoding="utf-8") as f:
                json.dump(self._stats_cache[manoir_id], f, indent=2, ensure_ascii=False)
        except IOError as e:
            logger.error(f"Erreur sauvegarde stats {manoir_id}: {e}")

    def get_priority_order(self, manoir_id: str, template_name: str) -> List[str]:
        """Retourne l'ordre de priorité des variantes pour un template"""
        stats = self.load_stats(manoir_id)

        if template_name in stats:
            return stats[template_name].get("priority_order", [])

        return []

    def record_match(self, manoir_id: str, template_name: str, variant_filename: str):
        """Enregistre un match réussi pour une variante

        Met à jour les hits et l'ordre de priorité.
        """
        stats = self.load_stats(manoir_id)

        if template_name not in stats:
            stats[template_name] = {
                "priority_order": [],
                "hits": {},
                "last_match": None
            }

        template_stats = stats[template_name]

        # Incrémenter les hits
        if variant_filename not in template_stats["hits"]:
            template_stats["hits"][variant_filename] = 0
        template_stats["hits"][variant_filename] += 1

        # Mettre à jour last_match
        template_stats["last_match"] = variant_filename

        # Recalculer l'ordre de priorité (triée par hits décroissants)
        template_stats["priority_order"] = sorted(
            template_stats["hits"].keys(),
            key=lambda v: template_stats["hits"][v],
            reverse=True
        )

        self._stats_cache[manoir_id] = stats
        self.save_stats(manoir_id)

    def clear_cache(self, manoir_id: str = None):
        """Vide le cache des stats"""
        if manoir_id:
            self._stats_cache.pop(manoir_id, None)
        else:
            self._stats_cache.clear()


class TemplateManager:
    """Gestionnaire principal des templates"""

    def __init__(self, templates_dir: Path = None):
        """
        Args:
            templates_dir: Dossier racine des templates (défaut: TEMPLATES_DIR)
        """
        self.templates_dir = templates_dir or TEMPLATES_DIR
        self._config_cache: Dict[str, TemplateConfig] = {}
        self._stats_manager = TemplateStatsManager()

    def _find_template_dir(self, template_name: str) -> Optional[Path]:
        """Trouve le dossier d'un template par son nom

        Cherche dans toutes les catégories (sous-dossiers de templates/).

        Args:
            template_name: Nom du template (ex: "bouton_ok")

        Returns:
            Path vers le dossier du template ou None
        """
        # Chercher dans chaque catégorie
        for category_dir in self.templates_dir.iterdir():
            if category_dir.is_dir():
                template_dir = category_dir / template_name
                if template_dir.is_dir() and (template_dir / "config.json").exists():
                    return template_dir

        return None

    def _load_config(self, template_dir: Path) -> Optional[TemplateConfig]:
        """Charge la configuration d'un template depuis son dossier"""
        config_file = template_dir / "config.json"

        if not config_file.exists():
            return None

        try:
            with open(config_file, encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Erreur lecture config {config_file}: {e}")
            return None

        # Déduire la catégorie du dossier parent
        category = template_dir.parent.name

        return TemplateConfig(
            name=data.get("name", template_dir.name),
            description=data.get("description", ""),
            category=category,
            base_path=template_dir,
            group_configs=data.get("group_configs", {})
        )

    def get_template_config(self, template_name: str) -> Optional[TemplateConfig]:
        """Récupère la configuration d'un template (avec cache)

        Args:
            template_name: Nom du template

        Returns:
            TemplateConfig ou None si non trouvé
        """
        if template_name in self._config_cache:
            return self._config_cache[template_name]

        template_dir = self._find_template_dir(template_name)
        if not template_dir:
            logger.debug(f"Template non trouvé: {template_name}")
            return None

        config = self._load_config(template_dir)
        if config:
            self._config_cache[template_name] = config

        return config

    def get_manoir_groups(self, manoir: "ManoirBase") -> List[str]:
        """Récupère la liste des groupes d'un manoir via son héritage

        Parcourt la chaîne d'héritage (MRO) et collecte les attributs 'group'.

        Args:
            manoir: Instance du manoir

        Returns:
            Liste des groupes (du plus spécifique au plus général)
        """
        groups = []

        # Parcourir le MRO (Method Resolution Order) de la classe
        for cls in type(manoir).__mro__:
            if hasattr(cls, "group") and cls.group:
                group = cls.group
                if group not in groups:
                    groups.append(group)

        return groups

    def resolve_variants(
        self,
        template_name: str,
        manoir: "ManoirBase"
    ) -> List[VariantConfig]:
        """Résout les variantes d'un template pour un manoir donné

        Cumule les variantes de tous les groupes du manoir et les trie
        selon la priorisation dynamique.

        Args:
            template_name: Nom du template
            manoir: Instance du manoir

        Returns:
            Liste de VariantConfig triées par priorité

        Raises:
            ValueError: Si aucun groupe compatible n'est trouvé
        """
        config = self.get_template_config(template_name)
        if not config:
            raise ValueError(f"Template non trouvé: {template_name}")

        # Récupérer les groupes du manoir
        manoir_groups = self.get_manoir_groups(manoir)

        if not manoir_groups:
            raise ValueError(f"Aucun groupe défini pour le manoir {manoir.manoir_id}")

        # Récupérer les variantes cumulées
        variants = config.get_variants_for_groups(manoir_groups)

        if not variants:
            raise ValueError(
                f"Aucune variante compatible pour {template_name} "
                f"(groupes manoir: {manoir_groups}, "
                f"groupes template: {list(config.group_configs.keys())})"
            )

        # Appliquer la priorisation dynamique
        priority_order = self._stats_manager.get_priority_order(
            manoir.manoir_id,
            template_name
        )

        if priority_order:
            # Trier les variantes selon l'ordre de priorité
            def priority_key(v: VariantConfig) -> int:
                try:
                    return priority_order.index(v.filename)
                except ValueError:
                    return len(priority_order)  # À la fin si pas dans la liste

            variants.sort(key=priority_key)

        return variants

    def record_match(self, manoir: "ManoirBase", template_name: str, variant_filename: str):
        """Enregistre un match réussi pour les stats

        Args:
            manoir: Instance du manoir
            template_name: Nom du template
            variant_filename: Nom du fichier de la variante qui a matché
        """
        self._stats_manager.record_match(
            manoir.manoir_id,
            template_name,
            variant_filename
        )

    def list_templates(self, category: str = None) -> List[str]:
        """Liste tous les templates disponibles

        Args:
            category: Filtrer par catégorie (optionnel)

        Returns:
            Liste des noms de templates
        """
        templates = []

        for category_dir in self.templates_dir.iterdir():
            if not category_dir.is_dir():
                continue

            if category and category_dir.name != category:
                continue

            for template_dir in category_dir.iterdir():
                if template_dir.is_dir() and (template_dir / "config.json").exists():
                    templates.append(template_dir.name)

        return sorted(templates)

    def list_categories(self) -> List[str]:
        """Liste toutes les catégories de templates

        Returns:
            Liste des noms de catégories
        """
        categories = set()

        for category_dir in self.templates_dir.iterdir():
            if category_dir.is_dir():
                # Vérifier qu'il y a au moins un template dans cette catégorie
                for template_dir in category_dir.iterdir():
                    if template_dir.is_dir() and (template_dir / "config.json").exists():
                        categories.add(category_dir.name)
                        break

        return sorted(categories)

    def list_groups(self) -> List[str]:
        """Liste tous les groupes utilisés dans les templates

        Returns:
            Liste des noms de groupes
        """
        groups = set()

        for template_name in self.list_templates():
            config = self.get_template_config(template_name)
            if config:
                groups.update(config.group_configs.keys())

        return sorted(groups)

    def clear_cache(self):
        """Vide le cache des configurations"""
        self._config_cache.clear()
        self._stats_manager.clear_cache()

    def reload_template(self, template_name: str):
        """Recharge la configuration d'un template"""
        self._config_cache.pop(template_name, None)


# Instance globale
_template_manager_instance = None


def get_template_manager() -> TemplateManager:
    """Retourne une instance singleton de TemplateManager

    Returns:
        TemplateManager: Instance partagée
    """
    global _template_manager_instance
    if _template_manager_instance is None:
        _template_manager_instance = TemplateManager()
    return _template_manager_instance
