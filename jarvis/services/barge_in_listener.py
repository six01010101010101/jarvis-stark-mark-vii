"""Monitor de interrupção por voz em tempo real (Barge-in / 'Jarvis, pare')."""

from __future__ import annotations

import logging
import threading
from typing import Callable
from jarvis.text_utils import normalize

logger = logging.getLogger(__name__)

BARGE_IN_STOP_PHRASES: frozenset[str] = frozenset({
    "jarvis pare", "pare jarvis", "pare de falar jarvis", "jarvis pare de falar",
    "jarvis para", "para jarvis", "para de falar jarvis", "jarvis para de falar",
    "silencio jarvis", "jarvis silencio", "silencio", "silêncio",
    "stop jarvis", "jarvis stop", "stop", "pare", "para", "chega", "cancela",
})


class BargeInListener:
    """Escuta paralela instantânea para cortar a fala do assistente ao comando do usuário."""

    def __init__(self, on_stop_callback: Callable[[], None] | None = None) -> None:
        self.on_stop = on_stop_callback
        self._is_monitoring = False
        self._lock = threading.Lock()

    def set_on_stop(self, callback: Callable[[], None]) -> None:
        self.on_stop = callback

    def is_stop_phrase(self, utterance: str) -> bool:
        """Avalia se a oração falada contém um gatilho de interrupção imediata."""
        norm = normalize(utterance)
        if norm in BARGE_IN_STOP_PHRASES:
            return True
        return any(phrase in norm for phrase in BARGE_IN_STOP_PHRASES)

    def notify_utterance(self, utterance: str) -> bool:
        """Processa a oração capturada e, se for comando de parada, aciona a interrupção imediata."""
        if self.is_stop_phrase(utterance):
            logger.info("Gatilho de interrupção detectado via voz: '%s'", utterance)
            if self.on_stop:
                try:
                    self.on_stop()
                except Exception as exc:
                    logger.error("Erro ao disparar callback de parada: %s", exc)
            return True
        return False
