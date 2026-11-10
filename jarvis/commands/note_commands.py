"""Comandos de anotações por voz e resumo conversacional integrados."""

from __future__ import annotations

import re

from jarvis.commands.registry import Command, CommandContext, Outcome
from jarvis.services.note_service import NoteService
from jarvis.services.rolling_transcript import GLOBAL_TRANSCRIPT

_DEFAULT_NOTE_SERVICE = NoteService()

_PREFIX_PATTERNS = (
    r"^anotar(?:\s+que|\s+isso|\s+o\s+seguinte|\s+uma\s+nota)?\s*",
    r"^anote(?:\s+que|\s+isso|\s+o\s+seguinte|\s+uma\s+nota)?\s*",
    r"^criar\s+nota(?:\s+de|\s+para)?\s*",
    r"^cria\s+uma\s+nota(?:\s+de|\s+para)?\s*",
    r"^salvar\s+nota(?:\s+de|\s+para)?\s*",
    r"^guardar\s+nota(?:\s+de|\s+para)?\s*",
    r"^fazer\s+anotacao(?:\s+de|\s+para)?\s*",
)


def _extract_note_body(utterance: str) -> str:
    """Extrai o texto da anotação removendo o comando de gatilho inicial."""
    cleaned = utterance.strip()
    for pattern in _PREFIX_PATTERNS:
        replaced = re.sub(pattern, "", cleaned, flags=re.IGNORECASE).strip()
        if replaced != cleaned:
            return replaced
    return ""


def _record_note(ctx: CommandContext, utterance: str, service: NoteService = _DEFAULT_NOTE_SERVICE) -> Outcome:
    body = _extract_note_body(utterance)
    if not body:
        ctx.reply("O que o senhor gostaria de anotar?", pending_intent="record_note")
        return Outcome.CONTINUE

    feedback = service.record_note(body)
    ctx.reply(feedback)
    return Outcome.CONTINUE


def _list_notes(ctx: CommandContext, _utterance: str, service: NoteService = _DEFAULT_NOTE_SERVICE) -> Outcome:
    feedback = service.list_notes()
    ctx.reply(feedback)
    return Outcome.CONTINUE


def _clear_notes(ctx: CommandContext, _utterance: str, service: NoteService = _DEFAULT_NOTE_SERVICE) -> Outcome:
    feedback = service.clear_notes()
    ctx.reply(feedback)
    return Outcome.CONTINUE


def _conversation_summary(ctx: CommandContext, _utterance: str) -> Outcome:
    feedback = GLOBAL_TRANSCRIPT.get_summary()
    ctx.reply(feedback)
    return Outcome.CONTINUE


def note_commands(service: NoteService | None = None) -> list[Command]:
    """Retorna a coleção de comandos de voz para anotações e histórico."""
    active_service = service or _DEFAULT_NOTE_SERVICE
    return [
        Command(
            "record_note",
            (
                "anotar",
                "anote",
                "criar nota",
                "cria uma nota",
                "salvar nota",
                "guardar nota",
                "fazer anotacao",
            ),
            lambda ctx, utt: _record_note(ctx, utt, active_service),
        ),
        Command(
            "list_notes",
            (
                "minhas notas",
                "ler notas",
                "quais sao minhas notas",
                "listar notas",
                "ver notas",
                "ler anotacoes",
                "minhas anotacoes",
            ),
            lambda ctx, utt: _list_notes(ctx, utt, active_service),
        ),
        Command(
            "clear_notes",
            (
                "limpar notas",
                "apagar notas",
                "deletar notas",
                "apagar anotacoes",
                "limpar anotacoes",
            ),
            lambda ctx, utt: _clear_notes(ctx, utt, active_service),
        ),
        Command(
            "conversation_summary",
            (
                "o que conversamos hoje",
                "o que falamos hoje",
                "resumo de hoje",
                "resumo das conversas",
                "lembrar conversas",
                "historico da conversa",
                "o que conversamos",
            ),
            _conversation_summary,
        ),
    ]
