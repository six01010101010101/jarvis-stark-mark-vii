"""Buffer circular de transcrições recentes para contexto conversacional contínuo."""

from __future__ import annotations

import threading
from collections import deque
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TranscriptTurn:
    """Registro temporal de uma fala do usuário ou resposta do Jarvis."""

    role: str
    text: str
    timestamp: datetime

    def format_line(self) -> str:
        hora = self.timestamp.strftime("%H:%M")
        origem = "Senhor Ken" if self.role == "user" else "Jarvis"
        return f"[{hora}] {origem}: {self.text}"


class RollingTranscriptBuffer:
    """Mantém as últimas interações na memória RAM para consulta contextual imediata (0ms)."""

    def __init__(self, max_turns: int = 25) -> None:
        self._max_turns = max_turns
        self._lock = threading.Lock()
        self._buffer: deque[TranscriptTurn] = deque(maxlen=max_turns)

    def add_turn(self, role: str, text: str) -> None:
        """Registra uma nova fala no buffer temporal."""
        clean = text.strip()
        if not clean:
            return
        turn = TranscriptTurn(role=role, text=clean, timestamp=datetime.now())
        with self._lock:
            self._buffer.append(turn)

    def get_recent_turns(self, count: int = 6) -> list[TranscriptTurn]:
        """Retorna os últimos N registros em ordem cronológica."""
        with self._lock:
            items = list(self._buffer)
            return items[-count:] if len(items) > count else items

    def get_summary(self, max_items: int = 8) -> str:
        """Formata um resumo das interações recentes para ser lido em voz alta."""
        turns = self.get_recent_turns(max_items)
        if not turns:
            return "Ainda não temos registros de conversas recentes nesta sessão, senhor."

        lines = [turn.format_line() for turn in turns]
        return "Aqui está o resumo das nossas interações recentes, senhor:\n" + "\n".join(lines)

    def get_last_user_query(self) -> str | None:
        """Retorna a última pergunta ou comando feito pelo usuário."""
        with self._lock:
            for turn in reversed(self._buffer):
                if turn.role == "user":
                    return turn.text
        return None

    def clear(self) -> None:
        """Limpa o buffer volátil."""
        with self._lock:
            self._buffer.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._buffer)


# Instância global do buffer de transcrição recente
GLOBAL_TRANSCRIPT = RollingTranscriptBuffer()
