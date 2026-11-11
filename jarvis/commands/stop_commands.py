"""Comandos prioritários para interromper a fala do J.A.R.V.I.S. imediatamente ('Jarvis, pare')."""

from __future__ import annotations

import logging

from jarvis.commands.registry import Command, CommandContext, Outcome

logger = logging.getLogger(__name__)


def _stop_speech(ctx: CommandContext, _utterance: str) -> Outcome:
    """Interrompe qualquer fala em reprodução, silencia o motor e fecha a janela de diálogo."""
    if hasattr(ctx.speaker, "stop"):
        try:
            ctx.speaker.stop()
        except Exception as exc:
            logger.debug("Erro ao parar speaker: %s", exc)

    if ctx.session and hasattr(ctx.session, "close_dialogue"):
        ctx.session.close_dialogue()

    ctx.view.show_status("PARADO // SILENCIANDO")
    return Outcome.CONTINUE


def stop_commands() -> list[Command]:
    """Retorna os comandos de interrupção imediata de fala."""
    return [
        Command(
            "stop_speech",
            (
                "jarvis pare", "jarvis para", "pare", "parar", "para de falar",
                "silencio", "silêncio", "cala a boca", "chega de falar", "cancela conversa", "cancela tudo",
            ),
            _stop_speech,
        ),
    ]
