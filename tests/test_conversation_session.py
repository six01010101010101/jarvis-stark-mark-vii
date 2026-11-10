"""Testes unitários para o gerenciador de sessão de conversa contínua (Multi-turn)."""

from __future__ import annotations

import time
import pytest

from jarvis.services.conversation_session import ConversationSession


def test_conversation_session_lifecycle() -> None:
    session = ConversationSession(timeout_seconds=2.0)
    assert not session.is_active()
    assert not session.is_awaiting_answer()

    # Inicia diálogo aguardando resposta
    session.start_dialogue(awaiting_answer=True)
    assert session.is_active()
    assert session.is_awaiting_answer()

    # Marca interação normal
    session.mark_interaction(awaiting_answer=False)
    assert session.is_active()
    assert not session.is_awaiting_answer()

    # Encerra diálogo
    session.close_dialogue()
    assert not session.is_active()


def test_conversation_session_timeout() -> None:
    session = ConversationSession(timeout_seconds=0.05)
    session.start_dialogue(awaiting_answer=True)
    assert session.is_active()

    time.sleep(0.08)
    # Após o timeout, volta a ser inativo
    assert not session.is_active()


def test_is_close_phrase_detection() -> None:
    session = ConversationSession()
    assert session.is_close_phrase("obrigado")
    assert session.is_close_phrase("era só isso")
    assert session.is_close_phrase("valeu jarvis")
    assert session.is_close_phrase("cancela")
    assert session.is_close_phrase("pode descansar")
    assert not session.is_close_phrase("abrir bloco de notas")
    assert not session.is_close_phrase("sim, abra o site")
