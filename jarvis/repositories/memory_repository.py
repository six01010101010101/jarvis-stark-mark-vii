"""Repositório de memória persistente, histórico de conversas e cache de intenções."""

from __future__ import annotations

import sqlite3
from typing import Any

from jarvis.database.connection import DatabaseConnection


class MemoryRepository:
    """Acesso a dados para memórias de longo prazo, conversas e cache no SQLite."""

    def __init__(self, db: DatabaseConnection, cloud_sync: object | None = None) -> None:
        self._db = db
        self._cloud_sync = cloud_sync

    @property
    def _conn(self) -> sqlite3.Connection:
        return self._db.get_connection()

    def set_memory(self, key: str, value: str, category: str = "general") -> None:
        """Salva ou atualiza uma memória sobre o usuário ou preferência."""
        sql = """
        INSERT INTO memories (key, value, category, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(key) DO UPDATE SET
            value = excluded.value,
            category = excluded.category,
            updated_at = CURRENT_TIMESTAMP;
        """
        with self._conn:
            self._conn.execute(sql, (key.strip().lower(), value.strip(), category))
        if self._cloud_sync and hasattr(self._cloud_sync, "sync_memory_async"):
            self._cloud_sync.sync_memory_async(key, value, category)

    def get_memory(self, key: str) -> str | None:
        """Recupera o valor de uma memória pela chave."""
        cur = self._conn.execute(
            "SELECT value FROM memories WHERE key = ? LIMIT 1;",
            (key.strip().lower(),),
        )
        row = cur.fetchone()
        return str(row["value"]) if row else None

    def get_all_memories(self) -> list[dict[str, Any]]:
        """Retorna todas as memórias gravadas."""
        cur = self._conn.execute(
            "SELECT key, value, category, updated_at FROM memories ORDER BY category, key;"
        )
        return [dict(row) for row in cur.fetchall()]

    def record_message(self, role: str, content: str) -> None:
        """Grava uma interação no histórico de conversas."""
        with self._conn:
            self._conn.execute(
                "INSERT INTO conversations (role, content) VALUES (?, ?);",
                (role, content),
            )
        if self._cloud_sync and hasattr(self._cloud_sync, "sync_conversation_async"):
            self._cloud_sync.sync_conversation_async(role, content)

    def get_recent_history(self, limit: int = 10) -> list[dict[str, str]]:
        """Recupera as últimas mensagens trocadas."""
        cur = self._conn.execute(
            "SELECT role, content FROM conversations ORDER BY id DESC LIMIT ?;",
            (limit,),
        )
        rows = cur.fetchall()
        return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]

    def cache_intent(self, phrase: str, action: str, target: str, reply: str) -> None:
        """Armazena em cache o comando interpretado para aceleração futura (0ms)."""
        sql = """
        INSERT INTO intent_cache (phrase, action, target, reply, hit_count, updated_at)
        VALUES (?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
        ON CONFLICT(phrase) DO UPDATE SET
            hit_count = hit_count + 1,
            action = excluded.action,
            target = excluded.target,
            reply = excluded.reply,
            updated_at = CURRENT_TIMESTAMP;
        """
        with self._conn:
            self._conn.execute(sql, (phrase.strip().lower(), action, target, reply))

    def get_cached_intent(self, phrase: str) -> dict[str, str] | None:
        """Busca se uma frase idêntica já foi resolvida anteriormente com sucesso."""
        cur = self._conn.execute(
            "SELECT action, target, reply FROM intent_cache WHERE phrase = ? LIMIT 1;",
            (phrase.strip().lower(),),
        )
        row = cur.fetchone()
        if not row:
            return None
        return {"action": row["action"], "target": row["target"], "reply": row["reply"]}

    def record_telemetry_snapshot(self) -> dict[str, Any]:
        """Coleta telemetria em tempo real do SO e persiste na tabela telemetry_logs do SQLite."""
        from jarvis.services.machine_state import MachineStateMonitor
        snap = MachineStateMonitor().get_snapshot()
        sql = """
        INSERT INTO telemetry_logs (cpu_percent, ram_used_gb, ram_free_gb, disk_free_gb, power_status)
        VALUES (?, ?, ?, ?, ?);
        """
        with self._conn:
            self._conn.execute(
                sql,
                (
                    float(snap["ram_percent"]),
                    float(snap["ram_used_gb"]),
                    float(snap["ram_free_gb"]),
                    float(snap["disk_free_gb"]),
                    str(snap["power_status"]),
                ),
            )
        return dict(snap)
