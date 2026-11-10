"""Repositório para persistência de artefatos cognitivos (mapas mentais, flashcards, resumos)."""

from __future__ import annotations

import sqlite3
from typing import Any

from jarvis.database.connection import DatabaseConnection


class ArtifactRepository:
    """Armazena e recupera artefatos cognitivos e de estudo gerados pela IA."""

    def __init__(self, db: DatabaseConnection) -> None:
        self._db = db

    @property
    def _conn(self) -> sqlite3.Connection:
        return self._db.get_connection()

    def save_artifact(self, artifact_type: str, title: str, content: str, format_type: str = "markdown") -> int:
        """Salva um artefato (ex: mind_map, flashcards, sticky_notes, quiz, roadmap)."""
        sql = """
        INSERT INTO cognitive_artifacts (type, title, content, format)
        VALUES (?, ?, ?, ?);
        """
        with self._conn:
            cur = self._conn.execute(sql, (artifact_type, title, content, format_type))
            return int(cur.lastrowid or 0)

    def get_latest_artifact(self, artifact_type: str | None = None) -> dict[str, Any] | None:
        """Retorna o artefato gerado mais recentemente."""
        if artifact_type:
            sql = "SELECT * FROM cognitive_artifacts WHERE type = ? ORDER BY id DESC LIMIT 1;"
            params = (artifact_type,)
        else:
            sql = "SELECT * FROM cognitive_artifacts ORDER BY id DESC LIMIT 1;"
            params = ()

        cur = self._conn.execute(sql, params)
        row = cur.fetchone()
        return dict(row) if row else None

    def list_artifacts(self, limit: int = 15) -> list[dict[str, Any]]:
        """Lista os artefatos cognitivos mais recentes."""
        cur = self._conn.execute(
            "SELECT id, type, title, format, created_at FROM cognitive_artifacts ORDER BY id DESC LIMIT ?;",
            (limit,),
        )
        return [dict(r) for r in cur.fetchall()]
