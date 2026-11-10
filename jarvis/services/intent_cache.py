"""Cache de intenções e comandos frequentes em memória e SQLite para resposta em 0ms."""

from __future__ import annotations

import threading
from collections import OrderedDict
from typing import Any

from jarvis.repositories.memory_repository import MemoryRepository
from jarvis.text_utils import normalize


class IntentCache:
    """Cache thread-safe com prioridade em memória LRU e persistência em banco SQLite."""

    def __init__(self, repository: MemoryRepository, capacity: int = 256) -> None:
        self._repo = repository
        self._capacity = max(16, capacity)
        self._lock = threading.Lock()
        self._cache: OrderedDict[str, dict[str, str]] = OrderedDict()

    def get(self, phrase: str) -> dict[str, str] | None:
        """Busca a resolução da frase em memória (0ms); caso ausente, consulta o SQLite."""
        key = normalize(phrase)
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                return dict(self._cache[key])

        # Consulta no banco SQLite
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

        # Grava de forma persistente no SQLite
        self._repo.cache_intent(key, action, target, reply)

    def clear(self) -> None:
        """Limpa o cache em memória."""
        with self._lock:
            self._cache.clear()
