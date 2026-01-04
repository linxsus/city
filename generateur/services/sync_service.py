"""Service de synchronisation bidirectionnelle pour le générateur."""

import hashlib
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from .database_service import get_database_service
from .import_service import get_import_service


class SyncDirection(Enum):
    """Direction de synchronisation."""
    CODE_TO_DB = "code_to_db"
    DB_TO_CODE = "db_to_code"


class ChangeType(Enum):
    """Type de changement détecté."""
    NEW = "new"
    MODIFIED = "modified"
    DELETED = "deleted"
    CONFLICT = "conflict"


@dataclass
class SyncChange:
    """Représente un changement détecté."""
    file_path: str
    element_name: str
    element_type: str
    change_type: ChangeType
    details: dict


class SyncService:
    """Service pour synchroniser le code et la base de données."""

    def __init__(self):
        self.db = get_database_service()
        self.import_service = get_import_service()

    def compute_content_hash(self, content: str) -> str:
        """Calcule le hash SHA256 du contenu."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def get_file_mtime(self, file_path: str | Path) -> float:
        """Récupère le timestamp de modification d'un fichier."""
        path = Path(file_path)
        if path.exists():
            return path.stat().st_mtime
        return 0.0

    # === Détection des changements ===

    def detect_code_changes(self) -> list[SyncChange]:
        """
        Détecte les modifications manuelles dans les fichiers de code.

        Returns:
            Liste des changements détectés
        """
        changes = []

        # Récupérer les états, chemins et actions actuels
        etats = self.import_service.get_all_etats()
        chemins = self.import_service.get_all_chemins()
        actions = self.import_service.get_all_actions()

        # Préparer les données pour comparaison
        current_files = []

        for etat in etats:
            content_hash = self.compute_content_hash(etat.class_info.code_source)
            mtime = self.get_file_mtime(etat.fichier)
            current_files.append((etat.fichier, etat.nom, mtime, content_hash, "etat", etat))

        for chemin in chemins:
            content_hash = self.compute_content_hash(chemin.class_info.code_source)
            mtime = self.get_file_mtime(chemin.fichier)
            current_files.append((chemin.fichier, chemin.nom, mtime, content_hash, "chemin", chemin))

        for action in actions:
            content_hash = self.compute_content_hash(action.class_info.code_source)
            mtime = self.get_file_mtime(action.fichier)
            current_files.append((action.fichier, action.nom, mtime, content_hash, "action", action))

        # Comparer avec les versions stockées
        for file_path, name, mtime, content_hash, elem_type, elem in current_files:
            stored = self.db.get_file_version(file_path, name)

            if stored is None:
                # Nouveau fichier (non suivi)
                changes.append(SyncChange(
                    file_path=file_path,
                    element_name=name,
                    element_type=elem_type,
                    change_type=ChangeType.NEW,
                    details={
                        "current_hash": content_hash,
                        "current_mtime": mtime,
                        "element_data": elem.to_dict() if hasattr(elem, "to_dict") else {},
                    },
                ))
            elif stored["content_hash"] != content_hash:
                # Fichier modifié
                changes.append(SyncChange(
                    file_path=file_path,
                    element_name=name,
                    element_type=elem_type,
                    change_type=ChangeType.MODIFIED,
                    details={
                        "old_hash": stored["content_hash"],
                        "new_hash": content_hash,
                        "old_mtime": stored["file_mtime"],
                        "new_mtime": mtime,
                        "version": stored["version"],
                        "element_data": elem.to_dict() if hasattr(elem, "to_dict") else {},
                    },
                ))

        # Détecter les fichiers supprimés
        tracked_versions = self.db.get_all_file_versions()
        current_elements = {(f[0], f[1]) for f in current_files}

        for version in tracked_versions:
            key = (version["file_path"], version["element_name"])
            if key not in current_elements:
                changes.append(SyncChange(
                    file_path=version["file_path"],
                    element_name=version["element_name"],
                    element_type=version["element_type"],
                    change_type=ChangeType.DELETED,
                    details={
                        "last_hash": version["content_hash"],
                        "last_mtime": version["file_mtime"],
                        "version": version["version"],
                    },
                ))

        return changes

    def get_sync_status(self) -> dict:
        """
        Retourne le statut de synchronisation global.

        Returns:
            Dict avec le statut et les changements détectés
        """
        changes = self.detect_code_changes()

        new_count = sum(1 for c in changes if c.change_type == ChangeType.NEW)
        modified_count = sum(1 for c in changes if c.change_type == ChangeType.MODIFIED)
        deleted_count = sum(1 for c in changes if c.change_type == ChangeType.DELETED)
        conflict_count = sum(1 for c in changes if c.change_type == ChangeType.CONFLICT)

        return {
            "is_synced": len(changes) == 0,
            "changes_count": len(changes),
            "new": new_count,
            "modified": modified_count,
            "deleted": deleted_count,
            "conflicts": conflict_count,
            "changes": [
                {
                    "file_path": c.file_path,
                    "element_name": c.element_name,
                    "element_type": c.element_type,
                    "change_type": c.change_type.value,
                    "details": c.details,
                }
                for c in changes
            ],
        }

    # === Synchronisation ===

    def sync_from_code(self, element_name: str | None = None) -> dict:
        """
        Synchronise la base de données depuis le code.

        Args:
            element_name: Nom de l'élément à synchroniser (ou None pour tout)

        Returns:
            Dict avec le résultat de la synchronisation
        """
        synced = []
        errors = []

        # Récupérer les éléments actuels
        etats = self.import_service.get_all_etats()
        chemins = self.import_service.get_all_chemins()
        actions = self.import_service.get_all_actions()

        elements = []
        for etat in etats:
            if element_name is None or etat.nom == element_name:
                elements.append(("etat", etat))

        for chemin in chemins:
            if element_name is None or chemin.nom == element_name:
                elements.append(("chemin", chemin))

        for action in actions:
            if element_name is None or action.nom == element_name:
                elements.append(("action", action))

        for elem_type, elem in elements:
            try:
                content_hash = self.compute_content_hash(elem.class_info.code_source)
                mtime = self.get_file_mtime(elem.fichier)

                self.db.save_file_version(
                    file_path=elem.fichier,
                    element_type=elem_type,
                    element_name=elem.nom,
                    content_hash=content_hash,
                    file_mtime=mtime,
                    sync_direction=SyncDirection.CODE_TO_DB.value,
                )

                synced.append({
                    "name": elem.nom,
                    "type": elem_type,
                    "file": elem.fichier,
                })

            except Exception as e:
                errors.append({
                    "name": elem.nom,
                    "type": elem_type,
                    "error": str(e),
                })

        return {
            "success": len(errors) == 0,
            "synced_count": len(synced),
            "synced": synced,
            "errors": errors,
        }

    def sync_all(self) -> dict:
        """
        Synchronise tous les éléments du code vers la base de données.

        Returns:
            Dict avec le résultat de la synchronisation
        """
        return self.sync_from_code(element_name=None)

    def accept_change(self, file_path: str, element_name: str) -> dict:
        """
        Accepte un changement et met à jour la version stockée.

        Args:
            file_path: Chemin du fichier
            element_name: Nom de l'élément

        Returns:
            Dict avec le résultat
        """
        # Trouver l'élément correspondant
        etats = self.import_service.get_all_etats()
        chemins = self.import_service.get_all_chemins()
        actions = self.import_service.get_all_actions()

        element = None
        elem_type = None

        for etat in etats:
            if etat.fichier == file_path and etat.nom == element_name:
                element = etat
                elem_type = "etat"
                break

        if element is None:
            for chemin in chemins:
                if chemin.fichier == file_path and chemin.nom == element_name:
                    element = chemin
                    elem_type = "chemin"
                    break

        if element is None:
            for action in actions:
                if action.fichier == file_path and action.nom == element_name:
                    element = action
                    elem_type = "action"
                    break

        if element is None:
            return {
                "success": False,
                "error": f"Élément '{element_name}' non trouvé dans '{file_path}'",
            }

        content_hash = self.compute_content_hash(element.class_info.code_source)
        mtime = self.get_file_mtime(file_path)

        self.db.save_file_version(
            file_path=file_path,
            element_type=elem_type,
            element_name=element_name,
            content_hash=content_hash,
            file_mtime=mtime,
            sync_direction=SyncDirection.CODE_TO_DB.value,
        )

        return {
            "success": True,
            "message": f"Changement accepté pour '{element_name}'",
            "element_type": elem_type,
        }

    def ignore_change(self, file_path: str, element_name: str) -> dict:
        """
        Ignore un changement (supprime le tracking pour cet élément).

        Args:
            file_path: Chemin du fichier
            element_name: Nom de l'élément

        Returns:
            Dict avec le résultat
        """
        deleted = self.db.delete_file_version(file_path, element_name)

        return {
            "success": True,
            "deleted": deleted,
            "message": f"Tracking supprimé pour '{element_name}'" if deleted else "Élément non trouvé",
        }

    def get_element_history(self, element_name: str) -> dict:
        """
        Récupère l'historique de synchronisation d'un élément.

        Args:
            element_name: Nom de l'élément

        Returns:
            Dict avec l'historique
        """
        all_versions = self.db.get_all_file_versions()
        element_versions = [v for v in all_versions if v["element_name"] == element_name]

        return {
            "element_name": element_name,
            "versions": element_versions,
            "version_count": len(element_versions),
        }


# Singleton
_sync_service: SyncService | None = None


def get_sync_service() -> SyncService:
    """Retourne l'instance singleton du service de synchronisation."""
    global _sync_service
    if _sync_service is None:
        _sync_service = SyncService()
    return _sync_service
