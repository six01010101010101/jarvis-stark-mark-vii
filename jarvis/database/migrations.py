"""Migrações e criação do schema do banco de dados local do J.A.R.V.I.S."""

from __future__ import annotations

import logging
import sqlite3

logger = logging.getLogger(__name__)

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    value TEXT NOT NULL,
    category TEXT DEFAULT 'general',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cognitive_artifacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    format TEXT DEFAULT 'markdown',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS intent_cache (
    phrase TEXT PRIMARY KEY,
    action TEXT NOT NULL,
    target TEXT NOT NULL,
    reply TEXT NOT NULL,
    hit_count INTEGER DEFAULT 1,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS telemetry_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cpu_percent REAL DEFAULT 0.0,
    ram_used_gb REAL NOT NULL,
    ram_free_gb REAL NOT NULL,
    disk_free_gb REAL NOT NULL,
    power_status TEXT NOT NULL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS listener_settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    state INTEGER DEFAULT 1,
    sensitivity REAL DEFAULT 2.5,
    energy_threshold INTEGER DEFAULT 18,
    pause_threshold REAL DEFAULT 0.45,
    device_index INTEGER DEFAULT 1,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO listener_settings (id, state, sensitivity, energy_threshold, pause_threshold, device_index)
VALUES (1, 1, 2.5, 18, 0.45, 1);

CREATE INDEX IF NOT EXISTS idx_memories_key ON memories(key);
CREATE INDEX IF NOT EXISTS idx_artifacts_type ON cognitive_artifacts(type);
CREATE INDEX IF NOT EXISTS idx_conversations_timestamp ON conversations(timestamp);
CREATE INDEX IF NOT EXISTS idx_telemetry_time ON telemetry_logs(recorded_at);
"""


def run_migrations(conn: sqlite3.Connection) -> None:
    """Executa o script de inicialização das tabelas relacionais do assistente."""
    try:
        with conn:
            conn.executescript(SCHEMA_SQL)
        logger.info("Tabelas e índices do banco SQLite verificados com sucesso.")
    except sqlite3.Error as exc:
        logger.error("Erro ao aplicar migrações do banco de dados: %s", exc)
        raise
