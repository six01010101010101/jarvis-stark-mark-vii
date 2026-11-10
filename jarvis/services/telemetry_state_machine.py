"""Máquina de estados operacional com telemetria e notificações de ciclo de vida (inspirado no Sumo Telemetria)."""

from __future__ import annotations

import logging
import threading
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)


class AssistantState(Enum):
    """Estados operacionais do assistente J.A.R.V.I.S."""

    IDLE = "IDLE"
    LISTENING = "LISTENING"
    PATIENCE_WAIT = "PATIENCE_WAIT"
    PROCESSING = "PROCESSING"
    SPEAKING = "SPEAKING"
    ALERT = "ALERT"
    ERROR = "ERROR"


@dataclass(frozen=True)
class TransitionEvent:
    """Registro de telemetria de uma transição de estado."""

    from_state: AssistantState
    to_state: AssistantState
    reason: str
    timestamp: datetime


StateListener = Callable[[AssistantState, AssistantState, str], None]


class TelemetryStateMachine:
    """Máquina de estados com monitoramento de transições e notificação de observadores."""

    def __init__(self, initial_state: AssistantState = AssistantState.IDLE, max_history: int = 50) -> None:
        self._state = initial_state
        self._lock = threading.Lock()
        self._listeners: list[StateListener] = []
        self._history: deque[TransitionEvent] = deque(maxlen=max_history)
        self._start_time = time.monotonic()
        self._transitions_count = 0

    @property
    def current_state(self) -> AssistantState:
        with self._lock:
            return self._state

    def subscribe(self, listener: StateListener) -> None:
        """Registra um observador para ser notificado em cada transição."""
        with self._lock:
            if listener not in self._listeners:
                self._listeners.append(listener)

    def unsubscribe(self, listener: StateListener) -> None:
        """Remove um observador registrado."""
        with self._lock:
            if listener in self._listeners:
                self._listeners.remove(listener)

    def transition_to(self, new_state: AssistantState, reason: str = "") -> bool:
        """Executa a transição de estado, registra telemetria e dispara callbacks."""
        with self._lock:
            if self._state == new_state:
                return False

            old_state = self._state
            self._state = new_state
            self._transitions_count += 1
            event = TransitionEvent(
                from_state=old_state,
                to_state=new_state,
                reason=reason,
                timestamp=datetime.now(),
            )
            self._history.append(event)
            listeners_snapshot = list(self._listeners)

        logger.debug("Transição de estado: %s -> %s (Motivo: '%s')", old_state.value, new_state.value, reason)

        for callback in listeners_snapshot:
            try:
                callback(old_state, new_state, reason)
            except Exception as exc:  # noqa: BLE001
                logger.error("Erro no listener de telemetria: %s", exc)

        return True

    def get_history(self) -> list[TransitionEvent]:
        """Retorna histórico de transições."""
        with self._lock:
            return list(self._history)

    def get_telemetry_snapshot(self) -> dict[str, Any]:
        """Retorna snapshot das métricas operacionais da máquina de estados."""
        with self._lock:
            uptime = time.monotonic() - self._start_time
            return {
                "current_state": self._state.value,
                "transitions_count": self._transitions_count,
                "uptime_seconds": round(uptime, 2),
                "history_length": len(self._history),
            }


GLOBAL_STATE_MACHINE = TelemetryStateMachine()
