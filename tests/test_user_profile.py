"""Testes unitários para o perfil pessoal do Ken e atalhos diretos de contas."""

from __future__ import annotations

from pathlib import Path
import pytest

from jarvis.commands.registry import Outcome
from jarvis.commands.user_shortcuts import user_shortcuts
from jarvis.database.connection import DatabaseConnection
from jarvis.database.migrations import run_migrations
from jarvis.repositories.memory_repository import MemoryRepository
from jarvis.services.user_profile import KEN_PROFILE, UserProfile
from tests.fakes import make_context


@pytest.fixture
def mem_repo(tmp_path: Path) -> MemoryRepository:
    db = DatabaseConnection(tmp_path / "test_user.db")
    run_migrations(db.get_connection())
    return MemoryRepository(db)


def test_user_profile_sync_to_database(mem_repo: MemoryRepository) -> None:
    profile = KEN_PROFILE
    profile.sync_to_database(mem_repo)

    assert mem_repo.get_memory("whatsapp_number") == "5511981237033"
    assert mem_repo.get_memory("instagram_handle") == "dracos6x"
    assert mem_repo.get_memory("youtube_email") == "keekobayashi2005@gmail.com"
    assert mem_repo.get_memory("google_email") == "kenkobayashi2005@gmail.com"


def test_user_shortcuts_routing() -> None:
    ctx = make_context()
    cmds = {c.name: c for c in user_shortcuts()}

    # Instagram
    assert cmds["my_instagram"].matches("abrir meu instagram")
    assert cmds["my_instagram"].matches("meu insta")
    assert cmds["my_instagram"].matches("dracos6x")
    assert cmds["my_instagram"].handler(ctx, "abrir meu instagram") is Outcome.CONTINUE
    assert "instagram.com/dracos6x" in ctx.launcher.urls[0]  # type: ignore[attr-defined]

    # YouTube
    assert cmds["my_youtube"].matches("abrir meu youtube")
    assert cmds["my_youtube"].matches("meu youtube")
    assert cmds["my_youtube"].handler(ctx, "abrir meu youtube") is Outcome.CONTINUE
    assert "youtube.com" in ctx.launcher.urls[1]  # type: ignore[attr-defined]

    # WhatsApp
    assert cmds["my_whatsapp"].matches("abrir meu whatsapp")
    assert cmds["my_whatsapp"].matches("meu zap")
    assert cmds["my_whatsapp"].handler(ctx, "abrir meu whatsapp") is Outcome.CONTINUE
    assert "5511981237033" in ctx.launcher.urls[2]  # type: ignore[attr-defined]

    # Apagar mensagem
    assert cmds["clear_text"].matches("apagar mensagem")
    assert cmds["clear_text"].matches("apagar tudo")
    assert cmds["clear_text"].handler(ctx, "apagar mensagem") is Outcome.CONTINUE
