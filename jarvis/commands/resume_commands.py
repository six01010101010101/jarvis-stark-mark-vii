"""Comandos para retomar a fala interrompida e dar continuidade ao diálogo."""

from __future__ import annotations

import logging

from jarvis.commands.registry import Command, CommandContext, Outcome

logger = logging.getLogger(__name__)


def _resume_speech(ctx: CommandContext, _utterance: str) -> Outcome:
    """Retoma a oração que estava sendo dita antes de ser interrompida pelo usuário."""
    interrupted: str | None = None
    if ctx.session and hasattr(ctx.session, "get_interrupted_speech"):
        interrupted = ctx.session.get_interrupted_speech()

    if interrupted:
        ctx.reply(f"Retomando de onde paramos, senhor: {interrupted}")
        if ctx.session and hasattr(ctx.session, "clear_interrupted_speech"):
            ctx.session.clear_interrupted_speech()
        return Outcome.CONTINUE

    try:
        from jarvis.services.rolling_transcript import GLOBAL_TRANSCRIPT
        turns = GLOBAL_TRANSCRIPT.get_recent_turns(count=2)
        last_turn = next((t.text for t in reversed(turns) if t.role == "assistant"), None)
        if last_turn:
            ctx.reply(f"Prosseguindo com nosso raciocínio, senhor: {last_turn}")
            return Outcome.CONTINUE
    except Exception:
        pass

    ctx.reply("Estou ouvindo, senhor. Pode continuar ou me dizer sobre o que deseja falar.")
    return Outcome.CONTINUE


def resume_commands() -> list[Command]:
    """Retorna os comandos de voz para continuidade e retomada de diálogo."""
    return [
        Command(
            "resume_speech",
            (
                "retome a conversa", "retoma a conversa",
                "continue a falar jarvis", "continue jarvis", "jarvis continue",
                "volte a falar jarvis", "volte a falar", "jarvis volte a falar",
                "continue falando", "pode continuar", "prossiga jarvis", "manda ver jarvis",
            ),
            _resume_speech,
        ),
    ]
