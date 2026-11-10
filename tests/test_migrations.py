"""Testes unitários das migrações do banco SQLite e persistência do J.A.R.V.I.S."""

from __future__ import annotations

import sqlite3

from jarvis.database.migrations import run_migrations
from jarvis.services.telemetry import SystemTelemetry


def test_migrations_create_all_required_tables() -> None:
    conn = sqlite3.connect(":memory:")
    run_migrations(conn)

    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}

    expected = {"memories", "conversations", "cognitive_artifacts", "intent_cache", "telemetry_logs"}
    assert expected.issubset(tables)


def test_telemetry_snapshot_persists_to_database() -> None:
    conn = sqlite3.connect(":memory:")
    run_migrations(conn)

    telemetry = SystemTelemetry()
    telemetry.record_snapshot(conn)

    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM telemetry_logs")
    count = cursor.fetchone()[0]
    assert count == 1
