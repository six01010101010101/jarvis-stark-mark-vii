"""Testes de ponta a ponta do diálogo contínuo multi-turn e resolução de pendências."""

from __future__ import annotations

import threading

from jarvis.assistant import Assistant
from jarvis.commands import Outcome, build_registry
from jarvis.services.conversation_session import ConversationSession
from tests.fakes import make_context


def _build_test_assistant(session: ConversationSession) -> tuple[Assistant, object]:
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
    return ast, ctx


def test_continuous_dialogue_without_repeating_wake_word() -> None:
    session = ConversationSession(timeout_seconds=30.0)
    ast, ctx = _build_test_assistant(session)

    # Fala sem wake word em repouso é ignorada
    assert ast.handle_phrase("abrir bloco de notas") is Outcome.CONTINUE
    assert ctx.launcher.launched == []  # type: ignore[attr-defined]

    # Inicia conversa dizendo 'Jarvis'
    ast.handle_phrase("jarvis")
    assert session.is_active() is True

    # Com a conversa aberta, comandos são executados sem repetir 'Jarvis'
    assert ast.handle_phrase("abrir bloco de notas") is Outcome.CONTINUE
    assert ctx.launcher.launched == ["notepad.exe"]  # type: ignore[attr-defined]


def test_phonetic_wake_word_starts_continuous_dialogue() -> None:
    session = ConversationSession(timeout_seconds=30.0)
    ast, ctx = _build_test_assistant(session)

    # Inicia diálogo dizendo "chaves"
    assert ast.handle_phrase("chaves") is Outcome.CONTINUE
    assert session.is_active() is True
    assert session.is_awaiting_answer() is True

    # Próxima frase executa diretamente sem precisar repetir 'Jarvis'
    assert ast.handle_phrase("abrir calculadora") is Outcome.CONTINUE
    assert ctx.launcher.launched == ["calc.exe"]  # type: ignore[attr-defined]


def test_pending_open_app_question_resolves_isolated_reply() -> None:
    session = ConversationSession(timeout_seconds=30.0)
    ast, ctx = _build_test_assistant(session)

    # Usuário diz apenas "abrir"
    ast.handle_phrase("jarvis abrir")
    assert session.is_awaiting_answer() is True
    assert session.get_pending_intent() == "open_app"

    # Usuário responde isoladamente o nome do aplicativo
    ast.handle_phrase("bloco de notas")
    assert ctx.launcher.launched == ["notepad.exe"]  # type: ignore[attr-defined]


def test_pending_open_url_question_resolves_site_name() -> None:
    session = ConversationSession(timeout_seconds=30.0)
    ast, ctx = _build_test_assistant(session)

    # Pergunta de site pendente
    session.mark_interaction(awaiting_answer=True, pending_intent="open_url")
    assert session.get_pending_intent() == "open_url"

    # Usuário responde apenas com o nome do site
    ast.handle_phrase("globo")
    assert any("globo.com" in url for url in ctx.launcher.urls)  # type: ignore[attr-defined]


def test_closing_phrase_gracefully_terminates_session() -> None:
    session = ConversationSession(timeout_seconds=30.0)
    ast, ctx = _build_test_assistant(session)

    session.start_dialogue()
    assert session.is_active() is True

    assert ast.handle_phrase("valeu jarvis") is Outcome.CONTINUE
    assert session.is_active() is False
    assert ctx.speaker.spoken[-1] == "Às suas ordens, senhor. Conversa encerrada."  # type: ignore[attr-defined]
