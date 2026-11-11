"""Sincronização opcional em nuvem com Supabase (PostgREST) em segundo plano."""

from __future__ import annotations

import json
import logging
import threading
import urllib.error
import urllib.request
from typing import Any

logger = logging.getLogger(__name__)

TIMEOUT_SECONDS = 4.0


class SupabaseSyncService:
    """Sincroniza memórias e conversas do Jarvis com o Supabase sem bloquear a UI."""

    def __init__(self, supabase_url: str | None = None, supabase_key: str | None = None) -> None:
        self._url = (supabase_url or "").rstrip("/")
        self._key = supabase_key or ""

    @property
    def is_configured(self) -> bool:
        return bool(self._url and self._key)

    def _post(self, table: str, payload: dict[str, Any]) -> bool:
        if not self.is_configured:
            return False

        endpoint = f"{self._url}/rest/v1/{table}"
        data = json.dumps(payload).encode("utf-8")
        headers = {
            "apikey": self._key,
            "Authorization": f"Bearer {self._key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal,resolution=merge-duplicates",
            "User-Agent": "JarvisAssistant/1.0",
        }

        try:
            req = urllib.request.Request(endpoint, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
                return resp.status in (200, 201, 204)
        except Exception as exc:  # noqa: BLE001
            logger.debug("Sincronização Supabase (%s) pendente: %s", table, exc)
            return False

    def sync_memory_async(self, key: str, value: str, category: str = "general") -> None:
        """Envia memória para o Supabase em thread paralela (0ms no loop principal)."""
        if not self.is_configured:
            return

        def _worker() -> None:
            self._post("jarvis_memories", {"key": key, "value": value, "category": category})

        threading.Thread(target=_worker, name="supabase-sync-mem", daemon=True).start()

    def sync_conversation_async(self, role: str, content: str) -> None:
        """Envia interação para o Supabase em thread paralela."""
        if not self.is_configured:
            return

        def _worker() -> None:
            self._post("jarvis_conversations", {"role": role, "content": content})

        threading.Thread(target=_worker, name="supabase-sync-chat", daemon=True).start()

    def push_async(self, user_text: str, reply_text: str) -> None:
        """Envia o turno completo (usuário + resposta) em background (Fire-and-Forget)."""
        if not self.is_configured:
            return

        def _worker() -> None:
            if user_text.strip():
                self._post("jarvis_conversations", {"role": "user", "content": user_text.strip()})
            if reply_text.strip():
                self._post("jarvis_conversations", {"role": "assistant", "content": reply_text.strip()})

        threading.Thread(target=_worker, name="supabase-push-async", daemon=True).start()

    def sync_artifact_async(self, artifact_type: str, title: str, content: str, format_type: str = "markdown") -> None:
        """Envia artefato cognitivo para o Supabase em thread paralela."""
        if not self.is_configured:
            return

        def _worker() -> None:
            self._post(
                "jarvis_cognitive_artifacts",
                {"type": artifact_type, "title": title, "content": content, "format": format_type},
            )

        threading.Thread(target=_worker, name="supabase-sync-art", daemon=True).start()

    def sync_episodic_async(self, role: str, content: str, intent_type: str = "dialogue", lang: str = "pt") -> None:
        if not self.is_configured:
            return

        def _worker() -> None:
            self._post("jarvis_episodic_conversations", {"role": role, "content": content, "intent_type": intent_type, "language": lang})

        threading.Thread(target=_worker, name="supabase-sync-episodic", daemon=True).start()
