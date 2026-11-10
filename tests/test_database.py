"""Testes unitários para banco de dados local SQLite, repositórios e cache de intenção."""

from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.database.connection import DatabaseConnection
from jarvis.database.migrations import run_migrations
from jarvis.repositories.artifact_repository import ArtifactRepository
from jarvis.repositories.memory_repository import MemoryRepository
from jarvis.services.intent_cache import IntentCache


@pytest.fixture
def temp_db(tmp_path: Path) -> DatabaseConnection:
    db_file = tmp_path / "test_jarvis.db"
    db = DatabaseConnection(db_file)
    run_migrations(db.get_connection())
    return db


def test_migrations_create_expected_tables(temp_db: DatabaseConnection) -> None:
    conn = temp_db.get_connection()
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {row["name"] for row in cur.fetchall()}
    assert "memories" in tables
    assert "conversations" in tables
    assert "cognitive_artifacts" in tables
    assert "intent_cache" in tables


def test_memory_repository_crud(temp_db: DatabaseConnection) -> None:
    repo = MemoryRepository(temp_db)
    repo.set_memory("game_fav", "Fortnite", category="gaming")
    assert repo.get_memory("game_fav") == "Fortnite"
    assert repo.get_memory("GAME_FAV") == "Fortnite"
    assert repo.get_memory("inexistente") is None

    repo.set_memory("game_fav", "Elden Ring", category="gaming")
    assert repo.get_memory("game_fav") == "Elden Ring"

    all_mems = repo.get_all_memories()
    assert len(all_mems) == 1
    assert all_mems[0]["key"] == "game_fav"
    assert all_mems[0]["value"] == "Elden Ring"


def test_conversation_history(temp_db: DatabaseConnection) -> None:
    repo = MemoryRepository(temp_db)
    repo.record_message("user", "Oi Jarvis")
    repo.record_message("assistant", "Olá senhor Ken")

    history = repo.get_recent_history(limit=5)
    assert len(history) == 2
    assert history[0] == {"role": "user", "content": "Oi Jarvis"}
    assert history[1] == {"role": "assistant", "content": "Olá senhor Ken"}


def test_artifact_repository_operations(temp_db: DatabaseConnection) -> None:
    repo = ArtifactRepository(temp_db)
    art_id = repo.save_artifact("mind_map", "Universo", "mindmap\n  root((Universo))", "mermaid")
    assert art_id > 0

    latest = repo.get_latest_artifact("mind_map")
    assert latest is not None
    assert latest["title"] == "Universo"
    assert latest["type"] == "mind_map"
    assert latest["format"] == "mermaid"

    arts = repo.list_artifacts(limit=10)
    assert len(arts) == 1
    assert arts[0]["id"] == art_id


def test_intent_cache_memory_and_persistence(temp_db: DatabaseConnection) -> None:
    repo = MemoryRepository(temp_db)
    cache = IntentCache(repo, capacity=10)

    # Initial miss
    assert cache.get("abrir bloco de notas") is None

    # Put in cache
    cache.put("abrir bloco de notas", "open_app", "notepad.exe", "Abrindo Bloco de Notas.")

    # In-memory hit (0ms)
    hit = cache.get("abrir bloco de notas")
    assert hit is not None
    assert hit["action"] == "open_app"
    assert hit["target"] == "notepad.exe"

    # New cache instance reading from SQLite repository
    cache2 = IntentCache(repo, capacity=10)
    hit2 = cache2.get("abrir bloco de notas")
    assert hit2 is not None
    assert hit2["action"] == "open_app"
    assert hit2["target"] == "notepad.exe"


def test_registry_caching_dispatch(temp_db: DatabaseConnection) -> None:
    from jarvis.commands import build_registry
    from tests.fakes import FakeAnswers, make_context

    repo = MemoryRepository(temp_db)
    cache = IntentCache(repo)
    cache.put("jogar lolzinho", "open_app", "LeagueClient.exe", "Abrindo League of Legends, senhor.")

    answers = FakeAnswers()
    ctx = make_context(answers=answers)
    reg = build_registry(cache=cache)

    reg.dispatch(ctx, "jogar lolzinho")
    assert ctx.launcher.launched == ["LeagueClient.exe"]  # type: ignore[attr-defined]
    assert ctx.speaker.spoken[-1] == "Abrindo League of Legends, senhor."  # type: ignore[attr-defined]
    assert len(answers.questions) == 0  # Zero calls to Gemini STT, 0ms latency!

