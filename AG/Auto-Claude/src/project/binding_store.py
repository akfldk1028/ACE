"""
Project Session Binding Store
==============================

SQLite-based mapping between Auto-Claude projects and AutoGen Studio sessions.
AutoGen Studio has no project concept - all sessions belong to 'guestuser@gmail.com'.
This store tracks which AutoGen sessions belong to which Auto-Claude project.

Usage:
    from src.project.binding_store import BindingStore

    store = BindingStore()

    # Bind a session to a project
    store.bind_session(
        project_id="uuid-of-project",
        project_path="D:/Data/my-project",
        session_id=123,
        team_id=5  # optional
    )

    # Get all sessions for a project
    session_ids = store.get_sessions_for_project("uuid-of-project")

    # Get unbound sessions
    unbound = store.get_unbound_sessions([121, 122, 123, 124])
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import threading

# DB location
DATA_DIR = Path(__file__).parent.parent.parent / "data"
DB_PATH = DATA_DIR / "project_bindings.db"


class BindingStore:
    """SQLite store for project-session mappings."""

    _instance: Optional['BindingStore'] = None
    _lock = threading.Lock()

    def __new__(cls) -> 'BindingStore':
        """Singleton pattern for thread safety."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, '_initialized', False):
            return

        # Ensure data directory exists
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        self._conn_local = threading.local()
        self._init_db()
        self._initialized = True

    @property
    def _conn(self) -> sqlite3.Connection:
        """Thread-local connection."""
        if not hasattr(self._conn_local, 'conn') or self._conn_local.conn is None:
            self._conn_local.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
            self._conn_local.conn.row_factory = sqlite3.Row
        return self._conn_local.conn

    def _init_db(self) -> None:
        """Initialize database schema."""
        with self._conn:
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS project_session_map (
                    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id            TEXT NOT NULL,
                    project_path          TEXT NOT NULL,
                    autogen_session_id    INTEGER NOT NULL,
                    autogen_team_id       INTEGER,
                    bound_at              TEXT NOT NULL,
                    bound_by              TEXT DEFAULT 'auto',
                    UNIQUE(project_id, autogen_session_id)
                )
            """)
            # Index for fast lookups
            self._conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_project_id
                ON project_session_map(project_id)
            """)
            self._conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_session_id
                ON project_session_map(autogen_session_id)
            """)

    def bind_session(
        self,
        project_id: str,
        project_path: str,
        session_id: int,
        team_id: Optional[int] = None,
        bound_by: str = 'auto'
    ) -> bool:
        """
        Bind an AutoGen session to an Auto-Claude project.

        Args:
            project_id: Auto-Claude project UUID
            project_path: Filesystem path of the project
            session_id: AutoGen Studio session ID
            team_id: Optional team ID used in the session
            bound_by: 'auto' for automatic binding, 'manual' for user-initiated

        Returns:
            True if bound successfully, False if already bound
        """
        try:
            with self._conn:
                self._conn.execute("""
                    INSERT OR REPLACE INTO project_session_map
                    (project_id, project_path, autogen_session_id, autogen_team_id, bound_at, bound_by)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    project_id,
                    project_path,
                    session_id,
                    team_id,
                    datetime.utcnow().isoformat(),
                    bound_by
                ))
            return True
        except sqlite3.Error as e:
            print(f"[BindingStore] Error binding session: {e}")
            return False

    def unbind_session(self, project_id: str, session_id: int) -> bool:
        """
        Remove binding between a session and project.

        Args:
            project_id: Auto-Claude project UUID
            session_id: AutoGen Studio session ID

        Returns:
            True if unbound, False if not found
        """
        try:
            with self._conn:
                cursor = self._conn.execute("""
                    DELETE FROM project_session_map
                    WHERE project_id = ? AND autogen_session_id = ?
                """, (project_id, session_id))
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"[BindingStore] Error unbinding session: {e}")
            return False

    def get_sessions_for_project(self, project_id: str) -> List[int]:
        """
        Get all AutoGen session IDs bound to a project.

        Args:
            project_id: Auto-Claude project UUID

        Returns:
            List of AutoGen session IDs
        """
        try:
            cursor = self._conn.execute("""
                SELECT autogen_session_id FROM project_session_map
                WHERE project_id = ?
                ORDER BY bound_at DESC
            """, (project_id,))
            return [row['autogen_session_id'] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"[BindingStore] Error getting sessions: {e}")
            return []

    def get_bindings_for_project(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Get full binding info for all sessions in a project.

        Args:
            project_id: Auto-Claude project UUID

        Returns:
            List of binding records with all fields
        """
        try:
            cursor = self._conn.execute("""
                SELECT * FROM project_session_map
                WHERE project_id = ?
                ORDER BY bound_at DESC
            """, (project_id,))
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"[BindingStore] Error getting bindings: {e}")
            return []

    def get_unbound_sessions(self, all_session_ids: List[int]) -> List[int]:
        """
        Find which sessions are not bound to any project.

        Args:
            all_session_ids: List of all known AutoGen session IDs

        Returns:
            List of session IDs that are not bound to any project
        """
        if not all_session_ids:
            return []

        try:
            placeholders = ','.join('?' * len(all_session_ids))
            cursor = self._conn.execute(f"""
                SELECT DISTINCT autogen_session_id FROM project_session_map
                WHERE autogen_session_id IN ({placeholders})
            """, all_session_ids)
            bound_ids = {row['autogen_session_id'] for row in cursor.fetchall()}
            return [sid for sid in all_session_ids if sid not in bound_ids]
        except sqlite3.Error as e:
            print(f"[BindingStore] Error getting unbound sessions: {e}")
            return all_session_ids  # Return all as fallback

    def get_project_for_session(self, session_id: int) -> Optional[Dict[str, Any]]:
        """
        Find which project a session is bound to.

        Args:
            session_id: AutoGen Studio session ID

        Returns:
            Project info dict or None if unbound
        """
        try:
            cursor = self._conn.execute("""
                SELECT project_id, project_path, bound_at, bound_by
                FROM project_session_map
                WHERE autogen_session_id = ?
            """, (session_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            print(f"[BindingStore] Error getting project for session: {e}")
            return None

    def get_all_bindings(self) -> List[Dict[str, Any]]:
        """Get all bindings in the store."""
        try:
            cursor = self._conn.execute("""
                SELECT * FROM project_session_map
                ORDER BY bound_at DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"[BindingStore] Error getting all bindings: {e}")
            return []

    def clear_project_bindings(self, project_id: str) -> int:
        """
        Remove all bindings for a project.

        Args:
            project_id: Auto-Claude project UUID

        Returns:
            Number of bindings removed
        """
        try:
            with self._conn:
                cursor = self._conn.execute("""
                    DELETE FROM project_session_map
                    WHERE project_id = ?
                """, (project_id,))
            return cursor.rowcount
        except sqlite3.Error as e:
            print(f"[BindingStore] Error clearing project bindings: {e}")
            return 0


# Module-level singleton accessor
_store: Optional[BindingStore] = None


def get_binding_store() -> BindingStore:
    """Get the singleton BindingStore instance."""
    global _store
    if _store is None:
        _store = BindingStore()
    return _store
