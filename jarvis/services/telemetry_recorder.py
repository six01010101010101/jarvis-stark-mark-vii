"""Auxiliares de persistência e telemetria para gravação assíncrona de mensagens."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def record_initial_telemetry(memory: object | None) -> None:
    """Registra snapshot inicial de telemetria sem bloquear a thread principal."""
    if memory and hasattr(memory, "record_telemetry_snapshot"):
        try:
            memory.record_telemetry_snapshot()  # type: ignore[union-attr]
        except Exception as exc:
            logger.warning("Telemetria inicial indisponível: %s", exc)


def async_persist_user_message(ctx: object, text: str) -> None:
    """Persiste mensagem do usuário no banco e no histórico global respeitando modo privado."""
    from jarvis.commands.privacy_commands import is_private_mode
    from jarvis.services.rolling_transcript import GLOBAL_TRANSCRIPT

    if is_private_mode():
        return
    GLOBAL_TRANSCRIPT.add_turn("user", text)
    memory = getattr(ctx, "memory", None)
    if memory:
        record_fn = getattr(memory, "record_message_async", getattr(memory, "record_message", None))
        if record_fn:
            record_fn("user", text)
    messages = getattr(ctx, "messages", None)
    if messages:
        try:
            save_fn = getattr(messages, "save_async", getattr(messages, "save", None))
            if save_fn:
                save_fn(text)
        except Exception as exc:
            logger.warning("Aviso ao salvar transcrição: %s", exc)
