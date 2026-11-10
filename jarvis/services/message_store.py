"""Persistência das mensagens ditadas e interações em modo síncrono e Fire-and-Forget."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import threading
from typing import Callable

TIMESTAMP_FORMAT = "%d/%m/%Y %H:%M:%S"


class TextFileMessageStore:
    """Acrescenta mensagens com data/hora a um arquivo de texto UTF-8 sem bloquear a voz."""

    def __init__(self, path: Path, clock: Callable[[], datetime] = datetime.now) -> None:
        self._path = path
        self._clock = clock
        self._lock = threading.Lock()

    @property
    def path(self) -> Path:
        """Caminho do arquivo de destino."""
        return self._path

    def save(self, message: str) -> None:
        """Grava a mensagem no fim do arquivo."""
        cleaned = message.strip()
        if not cleaned:
            raise ValueError("A mensagem não pode ser vazia.")
        with self._lock:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with self._path.open("a", encoding="utf-8") as file:
                file.write(f"{self._clock().strftime(TIMESTAMP_FORMAT)} - {cleaned}\n")

    def save_async(self, message: str) -> None:
        """Dispara gravação em background (Fire-and-Forget) para latência zero na voz."""
        cleaned = message.strip()
        if not cleaned:
            return
        threading.Thread(target=self._safe_save, args=(cleaned,), daemon=True).start()

    def save_interaction(self, user_text: str, reply_text: str) -> None:
        """Salva o par pergunta/resposta em background."""
        def _worker() -> None:
            if user_text.strip():
                self._safe_save(f"[USER] {user_text.strip()}")
            if reply_text.strip():
                self._safe_save(f"[JARVIS] {reply_text.strip()}")

        threading.Thread(target=_worker, name="msg-store-async", daemon=True).start()

    def _safe_save(self, text: str) -> None:
        try:
            self.save(text)
        except Exception:
            pass
