"""Cache de intenções e comandos frequentes em memória e SQLite para resposta em 0ms."""

from __future__ import annotations

from collections import OrderedDict
import threading
from typing import Any

from jarvis.repositories.memory_repository import MemoryRepository
from jarvis.services.semantic_wake_analyzer import SemanticWakeAnalyzer
from jarvis.text_utils import normalize


class IntentCache:
    """Cache thread-safe com prioridade em memória LRU e persistência em banco SQLite."""

    def __init__(self, repository: MemoryRepository, capacity: int = 256) -> None:
        self._repo, self._capacity = repository, max(16, capacity)
        self._lock = threading.Lock()
        self._cache: OrderedDict[str, dict[str, str]] = OrderedDict()

    def get(self, phrase: str) -> dict[str, str] | None:
        """Busca resolução em memória (0ms); perguntas reais ignoram o cache estático."""
        if SemanticWakeAnalyzer.is_real_question(phrase):
            return None

        key = normalize(phrase)
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                return dict(self._cache[key])

        record = self._repo.get_cached_intent(key)
        if record:
            with self._lock:
                self._cache[key] = record
                self._cache.move_to_end(key)
                if len(self._cache) > self._capacity:
                    self._cache.popitem(last=False)
            return dict(record)
        return None

    def put(self, phrase: str, action: str, target: str, reply: str) -> None:
        """Salva a intenção resolvida na memória e sincroniza no SQLite."""
        key = normalize(phrase)
        data = {"action": action, "target": target, "reply": reply}
        with self._lock:
            self._cache[key] = data
            self._cache.move_to_end(key)
            if len(self._cache) > self._capacity:
                self._cache.popitem(last=False)

        self._repo.cache_intent(key, action, target, reply)

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
