"""Testes de parada imediata ('Jarvis, pare'), boas-vindas curtas e alternância de saudações com gírias."""

from __future__ import annotations

import threading

from jarvis.assistant import Assistant
from jarvis.commands import Outcome, build_registry
from jarvis.services.conversation_session import ConversationSession
from jarvis.services.stark_personality import (
    FIRST_WAKE_RESPONSE,
    SUBSEQUENT_WAKE_RESPONSES,
)
from tests.fakes import FakeListener, make_context


def test_first_call_vs_subsequent_calls_different_greetings() -> None:
    session = ConversationSession(timeout_seconds=30.0)
    ctx = make_context(session=session)
    ast = Assistant(
        ctx=ctx,
        wake_listener=ctx.listener,
        registry=build_registry(),
        user_name="Ken",
        wake_word="jarvis",
        stop_event=threading.Event(),
        session=session,
    )

    # 1ª chamada a 'Jarvis': fala a saudação hospitaleira com 'Oi, senhor, tudo bem?...'
    ast.handle_phrase("jarvis")
    assert len(ctx.speaker.spoken) == 1  # type: ignore[attr-defined]
    assert ctx.speaker.spoken[-1] == FIRST_WAKE_RESPONSE  # type: ignore[attr-defined]
    assert "tudo bem" in ctx.speaker.spoken[-1].lower()  # type: ignore[attr-defined]

    # 2ª chamada a 'Jarvis': fala uma variação descontraída com gírias (sem repetir a primeira!)
    ast.handle_phrase("jarvis")
    assert len(ctx.speaker.spoken) == 2  # type: ignore[attr-defined]
    assert ctx.speaker.spoken[-1] != FIRST_WAKE_RESPONSE  # type: ignore[attr-defined]
    assert ctx.speaker.spoken[-1] in SUBSEQUENT_WAKE_RESPONSES  # type: ignore[attr-defined]

    # 3ª chamada a 'Jarvis': fala outra variação descontraída
    ast.handle_phrase("jarvis")
    assert len(ctx.speaker.spoken) == 3  # type: ignore[attr-defined]
    assert ctx.speaker.spoken[-1] in SUBSEQUENT_WAKE_RESPONSES  # type: ignore[attr-defined]


def test_stop_command_halts_speech_and_closes_dialogue() -> None:
    session = ConversationSession(timeout_seconds=30.0)
    ctx = make_context(session=session)
    ast = Assistant(
        ctx=ctx,
        wake_listener=ctx.listener,
        registry=build_registry(),
        user_name="Ken",
        wake_word="jarvis",
        stop_event=threading.Event(),
        session=session,
    )

    session.start_dialogue()
    assert session.is_active() is True

    # Comando 'Jarvis, pare' encerra a fala e a sessão imediatamente
    res = ast.handle_phrase("jarvis pare")
    assert res is Outcome.CONTINUE
    assert session.is_active() is False


def test_welcome_greeting_on_introduce_for_ken() -> None:
    ctx = make_context()
    ast = Assistant(
        ctx=ctx,
        wake_listener=ctx.listener,
        registry=build_registry(),
        user_name="Ken",
        wake_word="jarvis",
        stop_event=threading.Event(),
    )
    ast.introduce()
    assert len(ctx.speaker.spoken) == 1  # type: ignore[attr-defined]
    assert ctx.speaker.spoken[0] == "Bem-vindo, Ken."  # type: ignore[attr-defined]
