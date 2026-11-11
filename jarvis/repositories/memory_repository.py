"""Repositório de memória persistente, histórico episódico, fatos semânticos e cache de comandos."""

from __future__ import annotations

from datetime import datetime
import re
import sqlite3
import threading
from typing import Any

from jarvis.database.connection import DatabaseConnection


class MemoryRepository:
    """Acesso a dados para memórias de longo prazo, conversas episódicas e cache no SQLite."""

    def __init__(self, db: DatabaseConnection, cloud_sync: object | None = None) -> None:
        self._db, self._cloud_sync, self._write_lock = db, cloud_sync, threading.Lock()

    @property
    def _conn(self) -> sqlite3.Connection:
        return self._db.get_connection()

    def set_memory(self, key: str, value: str, category: str = "general") -> None:
        sql = """
        INSERT INTO memories (key, value, category, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(key) DO UPDATE SET
            value = excluded.value, category = excluded.category, updated_at = CURRENT_TIMESTAMP;
        """
        with self._conn:
            self._conn.execute(sql, (key.strip().lower(), value.strip(), category))
        if self._cloud_sync and hasattr(self._cloud_sync, "sync_memory_async"):
            self._cloud_sync.sync_memory_async(key, value, category)

    def get_memory(self, key: str) -> str | None:
        cur = self._conn.execute("SELECT value FROM memories WHERE key = ? LIMIT 1;", (key.strip().lower(),))
        row = cur.fetchone()
        return str(row["value"]) if row else None

    def get_all_memories(self) -> list[dict[str, Any]]:
        cur = self._conn.execute("SELECT key, value, category, updated_at FROM memories ORDER BY category, key;")
        return [dict(row) for row in cur.fetchall()]

    def remember(self, key: str, value: str, category: str = "general") -> None:
        threading.Thread(target=self._safe_set_memory, args=(key, value, category), daemon=True).start()

    def _safe_set_memory(self, key: str, value: str, category: str) -> None:
        try:
            with self._write_lock:
                self.set_memory(key, value, category)
        except Exception:
            pass

    def record_message(self, role: str, content: str) -> None:
        with self._write_lock, self._conn:
            self._conn.execute("INSERT INTO conversations (role, content) VALUES (?, ?);", (role, content))
        if self._cloud_sync and hasattr(self._cloud_sync, "sync_conversation_async"):
            self._cloud_sync.sync_conversation_async(role, content)

    def record_message_async(self, role: str, content: str) -> None:
        threading.Thread(target=lambda: self.record_message(role, content), daemon=True).start()

    def get_recent_history(self, limit: int = 10) -> list[dict[str, str]]:
        cur = self._conn.execute("SELECT role, content FROM conversations ORDER BY id DESC LIMIT ?;", (limit,))
        return [{"role": r["role"], "content": r["content"]} for r in reversed(cur.fetchall())]

    def save_episodic_turn(self, user_text: str, reply: str, intent_type: str = "dialogue", lang: str = "pt") -> None:
        now = datetime.now().isoformat()
        with self._write_lock, self._conn:
            self._conn.execute(
                "INSERT INTO episodic_conversations (role, content, intent_type, language, created_at) VALUES (?, ?, ?, ?, ?)",
                ("user", user_text, intent_type, lang, now),
            )
            self._conn.execute(
                "INSERT INTO episodic_conversations (role, content, intent_type, language, created_at) VALUES (?, ?, ?, ?, ?)",
                ("assistant", reply, intent_type, lang, now),
            )
            self._extract_user_facts(user_text, now)
        if self._cloud_sync and hasattr(self._cloud_sync, "sync_episodic_async"):
            self._cloud_sync.sync_episodic_async("user", user_text, intent_type=intent_type, lang=lang)
            self._cloud_sync.sync_episodic_async("assistant", reply, intent_type=intent_type, lang=lang)

    def save_episodic_turn_async(self, user_text: str, reply: str, intent_type: str = "dialogue", lang: str = "pt") -> None:
        threading.Thread(target=lambda: self.save_episodic_turn(user_text, reply, intent_type, lang), daemon=True).start()

    def _extract_user_facts(self, text: str, timestamp: str) -> None:
        patterns = [
            (r"\b(?:meu projeto|estou criando|estou trabalhando em)\s+(.+)", "projeto_usuario"),
            (r"\b(?:eu gosto de|eu prefiro|minha meta e|meu objetivo e)\s+(.+)", "preferencia_usuario"),
            (r"\b(?:lembre que|guarde que|anote que)\s+(.+)", "memoria_explicita"),
        ]
        for pat, cat in patterns:
            m = re.search(pat, text, flags=re.IGNORECASE)
            if m:
                self._conn.execute(
                    "INSERT OR IGNORE INTO semantic_facts (category, fact, updated_at) VALUES (?, ?, ?)",
                    (cat, m.group(0).strip(), timestamp),
                )

    def get_recent_episodic_context(self, limit: int = 15) -> list[dict[str, str]]:
        cur = self._conn.execute("SELECT role, content FROM episodic_conversations ORDER BY id DESC LIMIT ?", (limit,))
        return [{"role": r["role"], "content": r["content"]} for r in reversed(cur.fetchall())]

    def get_learned_facts(self, limit: int = 15) -> list[str]:
        cur = self._conn.execute("SELECT fact FROM semantic_facts ORDER BY id DESC LIMIT ?", (limit,))
        return [str(r["fact"]) for r in cur.fetchall()]

    def cache_intent(self, phrase: str, action: str, target: str, reply: str) -> None:
        sql = """
        INSERT INTO intent_cache (phrase, action, target, reply, hit_count, updated_at)
        VALUES (?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
        ON CONFLICT(phrase) DO UPDATE SET
            hit_count = hit_count + 1, action = excluded.action, target = excluded.target,
            reply = excluded.reply, updated_at = CURRENT_TIMESTAMP;
        """
        with self._conn:
            self._conn.execute(sql, (phrase.strip().lower(), action, target, reply))

    def get_cached_intent(self, phrase: str) -> dict[str, str] | None:
        cur = self._conn.execute("SELECT action, target, reply FROM intent_cache WHERE phrase = ? LIMIT 1;", (phrase.strip().lower(),))
        row = cur.fetchone()
        return {"action": row["action"], "target": row["target"], "reply": row["reply"]} if row else None

    def record_telemetry_snapshot(self) -> dict[str, Any]:
        from jarvis.services.machine_state import MachineStateMonitor
        snap = MachineStateMonitor().get_snapshot()
        sql = "INSERT INTO telemetry_logs (cpu_percent, ram_used_gb, ram_free_gb, disk_free_gb, power_status) VALUES (?, ?, ?, ?, ?);"
        with self._conn:
            self._conn.execute(sql, (float(snap["ram_percent"]), float(snap["ram_used_gb"]), float(snap["ram_free_gb"]), float(snap["disk_free_gb"]), str(snap["power_status"])))
        return dict(snap)

    def save_goal(self, goal_id: str, title: str, description: str = "", status: str = "opened", priority: int = 1, category: str = "general") -> None:
        sql = """
        INSERT INTO hivemind_goals (goal_id, title, description, status, priority, category, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(goal_id) DO UPDATE SET
            title = excluded.title, description = excluded.description, status = excluded.status,
            priority = excluded.priority, category = excluded.category, updated_at = CURRENT_TIMESTAMP;
        """
        with self._write_lock, self._conn:
            self._conn.execute(sql, (goal_id.strip(), title.strip(), description.strip(), status, priority, category))

    def get_goals(self, status: str | None = None, limit: int = 10) -> list[dict[str, Any]]:
        sql = "SELECT goal_id, title, description, status, priority, category, created_at FROM hivemind_goals"
        params: tuple[Any, ...] = ()
        if status:
            sql += " WHERE status = ? ORDER BY priority DESC, id DESC LIMIT ?"
            params = (status, limit)
        else:
            sql += " ORDER BY status ASC, priority DESC, id DESC LIMIT ?"
            params = (limit,)
        cur = self._conn.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]

    def update_goal_status(self, goal_id: str, status: str) -> bool:
        sql = "UPDATE hivemind_goals SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE goal_id = ? OR LOWER(title) LIKE ?;"
        pattern = f"%{goal_id.strip().lower()}%"
        with self._write_lock, self._conn:
            cur = self._conn.execute(sql, (status, goal_id.strip(), pattern))
            return cur.rowcount > 0

    def upsert_graph_node(self, node_id: str, label: str, node_type: str, metadata: str = "{}") -> None:
        sql = """
        INSERT INTO knowledge_graph_nodes (node_id, label, node_type, metadata, updated_at)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(node_id) DO UPDATE SET
            label = excluded.label, node_type = excluded.node_type, metadata = excluded.metadata, updated_at = CURRENT_TIMESTAMP;
        """
        with self._write_lock, self._conn:
            self._conn.execute(sql, (node_id.strip().lower(), label.strip(), node_type.strip(), metadata))

    def upsert_graph_edge(self, source: str, target: str, relation: str, weight: float = 1.0) -> None:
        sql = """
        INSERT INTO knowledge_graph_edges (source_node, target_node, relation, weight, updated_at)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(source_node, target_node, relation) DO UPDATE SET
            weight = excluded.weight, updated_at = CURRENT_TIMESTAMP;
        """
        with self._write_lock, self._conn:
            self._conn.execute(sql, (source.strip().lower(), target.strip().lower(), relation.strip().lower(), weight))

    def get_graph_edges(self, source: str | None = None) -> list[dict[str, Any]]:
        if source:
            sql = "SELECT source_node, target_node, relation, weight FROM knowledge_graph_edges WHERE source_node = ? OR target_node = ?;"
            cur = self._conn.execute(sql, (source.strip().lower(), source.strip().lower()))
        else:
            sql = "SELECT source_node, target_node, relation, weight FROM knowledge_graph_edges LIMIT 50;"
            cur = self._conn.execute(sql)
        return [dict(r) for r in cur.fetchall()]
