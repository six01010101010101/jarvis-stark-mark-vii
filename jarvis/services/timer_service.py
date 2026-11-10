"""Serviço de temporizadores, cronômetros e alarmes de contagem regressiva."""

from __future__ import annotations

import logging
import threading
from typing import Callable

logger = logging.getLogger(__name__)


class TimerService:
    """Gerenciador thread-safe de alarmes e contagens regressivas em background."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._active_timers: dict[str, threading.Timer] = {}

    def set_timer(self, seconds: float, label: str, on_complete: Callable[[str], None]) -> str:
        """Agenda um temporizador e executa o callback ao término."""
        timer_id = f"timer_{label}_{int(seconds)}"

        def _target() -> None:
            with self._lock:
                self._active_timers.pop(timer_id, None)
            logger.info("Temporizador finalizado: %s (%ss)", label, seconds)
            on_complete(label)

        timer = threading.Timer(seconds, _target)
        timer.daemon = True

        with self._lock:
            # Cancela timer anterior com o mesmo rótulo se houver
            old_timer = self._active_timers.get(timer_id)
            if old_timer:
                old_timer.cancel()
            self._active_timers[timer_id] = timer

        timer.start()
        logger.info("Temporizador iniciado: %s por %s segundos", label, seconds)
        return timer_id

    def cancel_all(self) -> int:
        """Cancela todos os temporizadores em execução."""
        with self._lock:
            count = len(self._active_timers)
            for timer in self._active_timers.values():
                timer.cancel()
            self._active_timers.clear()
            return count

    def get_active_count(self) -> int:
        with self._lock:
            return len(self._active_timers)
