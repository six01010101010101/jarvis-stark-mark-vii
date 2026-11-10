"""Testes unitários para o serviço de sincronização em nuvem do Supabase."""

from __future__ import annotations

from pathlib import Path

from jarvis.database.connection import DatabaseConnection
from jarvis.database.migrations import run_migrations
from jarvis.repositories.memory_repository import MemoryRepository
from jarvis.services.supabase_sync import SupabaseSyncService


class FakeSupabaseSync:
    def __init__(self) -> None:
        self.memories: list[tuple[str, str, str]] = []
        self.conversations: list[tuple[str, str]] = []

    def sync_memory_async(self, key: str, value: str, category: str = "general") -> None:
        self.memories.append((key, value, category))

    def sync_conversation_async(self, role: str, content: str) -> None:
        self.conversations.append((role, content))


def test_supabase_sync_configuration_check() -> None:
    empty_sync = SupabaseSyncService()
    assert not empty_sync.is_configured

    configured_sync = SupabaseSyncService("https://test.supabase.co", "key_secret")
    assert configured_sync.is_configured


def test_memory_repository_delegates_to_cloud_sync(tmp_path: Path) -> None:
    db = DatabaseConnection(tmp_path / "sync_test.db")
    run_migrations(db.get_connection())

    fake_cloud = FakeSupabaseSync()
    repo = MemoryRepository(db, cloud_sync=fake_cloud)

    repo.set_memory("tema", "escuro", "ui")
    assert fake_cloud.memories == [("tema", "escuro", "ui")]

    repo.record_message("user", "olá jarvis")
    assert fake_cloud.conversations == [("user", "olá jarvis")]
