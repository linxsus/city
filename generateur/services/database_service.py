"""Service de base de données SQLite pour le générateur."""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

from ..config import GENERATED_DIR


class DatabaseService:
    """Service pour gérer la base de données SQLite du générateur."""

    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path or (GENERATED_DIR / "generator.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    @contextmanager
    def _get_connection(self):
        """Context manager pour les connexions à la base de données."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_database(self):
        """Initialise les tables de la base de données."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Table des sessions (brouillons)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_completed INTEGER DEFAULT 0
                )
            """)

            # Table des templates avec hash
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT UNIQUE NOT NULL,
                    dhash TEXT NOT NULL,
                    width INTEGER,
                    height INTEGER,
                    source TEXT DEFAULT 'framework',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Index pour recherche rapide par hash
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_templates_dhash
                ON templates(dhash)
            """)

            # Table des groupes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    color TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Table des erreurs connues
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS known_errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    type TEXT NOT NULL,
                    category TEXT,
                    message TEXT,
                    image_path TEXT,
                    text_pattern TEXT,
                    priority INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Table de l'historique des générations
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS generation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    class_name TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    template_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

    # === Sessions (Brouillons) ===

    def save_session(
        self,
        session_type: str,
        name: str,
        data: dict,
        session_id: int | None = None,
    ) -> int:
        """
        Sauvegarde ou met à jour une session.

        Args:
            session_type: Type de session (etat, chemin, action_longue)
            name: Nom de l'élément
            data: Données de la session
            session_id: ID de la session existante (pour mise à jour)

        Returns:
            ID de la session
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if session_id:
                cursor.execute("""
                    UPDATE sessions
                    SET name = ?, data = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (name, json.dumps(data), session_id))
                return session_id
            else:
                cursor.execute("""
                    INSERT INTO sessions (type, name, data)
                    VALUES (?, ?, ?)
                """, (session_type, name, json.dumps(data)))
                return cursor.lastrowid

    def get_session(self, session_id: int) -> dict | None:
        """Récupère une session par son ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
            row = cursor.fetchone()

            if row:
                return {
                    "id": row["id"],
                    "type": row["type"],
                    "name": row["name"],
                    "data": json.loads(row["data"]),
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "is_completed": bool(row["is_completed"]),
                }
            return None

    def list_sessions(
        self,
        session_type: str | None = None,
        include_completed: bool = False,
    ) -> list[dict]:
        """Liste les sessions."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM sessions WHERE 1=1"
            params = []

            if session_type:
                query += " AND type = ?"
                params.append(session_type)

            if not include_completed:
                query += " AND is_completed = 0"

            query += " ORDER BY updated_at DESC"

            cursor.execute(query, params)
            return [
                {
                    "id": row["id"],
                    "type": row["type"],
                    "name": row["name"],
                    "data": json.loads(row["data"]),
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "is_completed": bool(row["is_completed"]),
                }
                for row in cursor.fetchall()
            ]

    def complete_session(self, session_id: int) -> bool:
        """Marque une session comme complétée."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE sessions
                SET is_completed = 1, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (session_id,))
            return cursor.rowcount > 0

    def delete_session(self, session_id: int) -> bool:
        """Supprime une session."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            return cursor.rowcount > 0

    # === Templates avec Hash ===

    def save_template_hash(
        self,
        path: str,
        dhash: str,
        width: int | None = None,
        height: int | None = None,
        source: str = "framework",
    ) -> int:
        """
        Sauvegarde le hash d'un template.

        Args:
            path: Chemin relatif du template
            dhash: Hash perceptuel
            width: Largeur en pixels
            height: Hauteur en pixels
            source: Source (framework, generated, imported)

        Returns:
            ID du template
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO templates (path, dhash, width, height, source, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (path, dhash, width, height, source))
            return cursor.lastrowid

    def get_template_by_path(self, path: str) -> dict | None:
        """Récupère un template par son chemin."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM templates WHERE path = ?", (path,))
            row = cursor.fetchone()

            if row:
                return dict(row)
            return None

    def find_templates_by_hash(self, dhash: str, max_distance: int = 5) -> list[dict]:
        """
        Trouve les templates avec un hash similaire.

        Args:
            dhash: Hash à rechercher
            max_distance: Distance de Hamming maximale

        Returns:
            Liste des templates correspondants avec leur distance
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM templates")

            results = []
            for row in cursor.fetchall():
                distance = self._hamming_distance(dhash, row["dhash"])
                if distance <= max_distance:
                    template = dict(row)
                    template["distance"] = distance
                    template["similarity"] = 1 - (distance / 64)
                    results.append(template)

            results.sort(key=lambda x: x["distance"])
            return results

    def _hamming_distance(self, hash1: str, hash2: str) -> int:
        """Calcule la distance de Hamming entre deux hashes."""
        if len(hash1) != len(hash2):
            return 64

        try:
            int1 = int(hash1, 16)
            int2 = int(hash2, 16)
            xor = int1 ^ int2
            return bin(xor).count("1")
        except ValueError:
            return 64

    def list_templates(self, source: str | None = None) -> list[dict]:
        """Liste tous les templates."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if source:
                cursor.execute(
                    "SELECT * FROM templates WHERE source = ? ORDER BY path",
                    (source,),
                )
            else:
                cursor.execute("SELECT * FROM templates ORDER BY path")

            return [dict(row) for row in cursor.fetchall()]

    def delete_template(self, path: str) -> bool:
        """Supprime un template de la base de données."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM templates WHERE path = ?", (path,))
            return cursor.rowcount > 0

    # === Groupes ===

    def save_group(
        self,
        name: str,
        description: str | None = None,
        color: str | None = None,
    ) -> int:
        """Sauvegarde un groupe."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO groups (name, description, color)
                VALUES (?, ?, ?)
            """, (name, description, color))
            return cursor.lastrowid

    def get_group(self, name: str) -> dict | None:
        """Récupère un groupe par son nom."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM groups WHERE name = ?", (name,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def list_groups(self) -> list[dict]:
        """Liste tous les groupes."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM groups ORDER BY name")
            return [dict(row) for row in cursor.fetchall()]

    def delete_group(self, name: str) -> bool:
        """Supprime un groupe."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM groups WHERE name = ?", (name,))
            return cursor.rowcount > 0

    # === Erreurs Connues ===

    def save_known_error(
        self,
        name: str,
        error_type: str,
        category: str | None = None,
        message: str | None = None,
        image_path: str | None = None,
        text_pattern: str | None = None,
        priority: int = 0,
    ) -> int:
        """Sauvegarde une erreur connue."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO known_errors
                (name, type, category, message, image_path, text_pattern, priority)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (name, error_type, category, message, image_path, text_pattern, priority))
            return cursor.lastrowid

    def list_known_errors(self, category: str | None = None) -> list[dict]:
        """Liste les erreurs connues."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if category:
                cursor.execute(
                    "SELECT * FROM known_errors WHERE category = ? ORDER BY priority DESC, name",
                    (category,),
                )
            else:
                cursor.execute("SELECT * FROM known_errors ORDER BY priority DESC, name")

            return [dict(row) for row in cursor.fetchall()]

    # === Historique des Générations ===

    def log_generation(
        self,
        gen_type: str,
        name: str,
        class_name: str,
        file_path: str,
        template_path: str | None = None,
    ) -> int:
        """Enregistre une génération dans l'historique."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO generation_history
                (type, name, class_name, file_path, template_path)
                VALUES (?, ?, ?, ?, ?)
            """, (gen_type, name, class_name, file_path, template_path))
            return cursor.lastrowid

    def list_generation_history(
        self,
        gen_type: str | None = None,
        limit: int = 50,
    ) -> list[dict]:
        """Liste l'historique des générations."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM generation_history"
            params = []

            if gen_type:
                query += " WHERE type = ?"
                params.append(gen_type)

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    # === Recherche et Filtrage ===

    def search(self, query: str, tables: list[str] | None = None) -> dict:
        """
        Recherche globale dans la base de données.

        Args:
            query: Terme de recherche
            tables: Tables à rechercher (sessions, templates, groups, known_errors)

        Returns:
            Résultats par table
        """
        tables = tables or ["sessions", "templates", "groups", "known_errors"]
        results = {}
        search_pattern = f"%{query}%"

        with self._get_connection() as conn:
            cursor = conn.cursor()

            if "sessions" in tables:
                cursor.execute("""
                    SELECT * FROM sessions
                    WHERE name LIKE ? OR data LIKE ?
                    ORDER BY updated_at DESC LIMIT 20
                """, (search_pattern, search_pattern))
                results["sessions"] = [
                    {
                        "id": row["id"],
                        "type": row["type"],
                        "name": row["name"],
                        "updated_at": row["updated_at"],
                    }
                    for row in cursor.fetchall()
                ]

            if "templates" in tables:
                cursor.execute("""
                    SELECT * FROM templates
                    WHERE path LIKE ?
                    ORDER BY path LIMIT 50
                """, (search_pattern,))
                results["templates"] = [dict(row) for row in cursor.fetchall()]

            if "groups" in tables:
                cursor.execute("""
                    SELECT * FROM groups
                    WHERE name LIKE ? OR description LIKE ?
                    ORDER BY name
                """, (search_pattern, search_pattern))
                results["groups"] = [dict(row) for row in cursor.fetchall()]

            if "known_errors" in tables:
                cursor.execute("""
                    SELECT * FROM known_errors
                    WHERE name LIKE ? OR message LIKE ?
                    ORDER BY priority DESC, name
                """, (search_pattern, search_pattern))
                results["known_errors"] = [dict(row) for row in cursor.fetchall()]

        return results

    def get_stats(self) -> dict:
        """Retourne des statistiques sur la base de données."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            stats = {}

            cursor.execute("SELECT COUNT(*) FROM sessions WHERE is_completed = 0")
            stats["active_sessions"] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM templates")
            stats["templates"] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM groups")
            stats["groups"] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM known_errors")
            stats["known_errors"] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM generation_history")
            stats["total_generations"] = cursor.fetchone()[0]

            return stats


# Singleton
_database_service: DatabaseService | None = None


def get_database_service() -> DatabaseService:
    """Retourne l'instance singleton du service de base de données."""
    global _database_service
    if _database_service is None:
        _database_service = DatabaseService()
    return _database_service
