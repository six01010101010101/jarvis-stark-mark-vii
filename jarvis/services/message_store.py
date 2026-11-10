"""Persistência das mensagens ditadas pelo comando 'transcrever'."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Callable

TIMESTAMP_FORMAT = "%d/%m/%Y %H:%M:%S"


class TextFileMessageStore:
    """Acrescenta mensagens com data/hora a um arquivo de texto UTF-8."""

    def __init__(self, path: Path, clock: Callable[[], datetime] = datetime.now) -> None:
        self._path = path
        self._clock = clock

    @property
    def path(self) -> Path:
        """Caminho do arquivo de destino."""
        return self._path

    def save(self, message: str) -> None:
        """Grava a mensagem no fim do arquivo.

        Raises:
            ValueError: se a mensagem estiver vazia.
            OSError: se o arquivo não puder ser escrito.
        """
        cleaned = message.strip()
        if not cleaned:
            raise ValueError("A mensagem não pode ser vazia.")
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as file:
            file.write(f"{self._clock().strftime(TIMESTAMP_FORMAT)} - {cleaned}\n")
