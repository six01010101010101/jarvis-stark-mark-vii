"""Testes de alta precisão fonética para wake word do Jarvis (PT-BR)."""

from __future__ import annotations

import threading
import pytest

from jarvis.assistant import Assistant
from jarvis.commands import Outcome, build_registry
from jarvis.services.conversation_session import ConversationSession
from jarvis.services.speech_corrector import SpeechCorrector
from jarvis.text_utils import extract_wake_and_command, is_wake_word
from tests.fakes import make_context


@pytest.mark.parametrize(
    "token",
    [
        "jarvis", "jarbas", "iarvis", "jarves", "jarvi",
        "chave", "chaves", "chavez", "xave", "xaves", "xavez",
        "javi", "javis", "jabes", "charles", "davis", "davi", "travis",
    ],
)
def test_is_wake_word_detects_all_stt_variants(token: str) -> None:
    assert is_wake_word(token) is True


@pytest.mark.parametrize(
    ("utterance", "expected_has_wake", "expected_command"),
    [
        ("jarvis", True, ""),
        ("chaves", True, ""),
        ("chave", True, ""),
        ("já vi", True, ""),
        ("ja vi", True, ""),
        ("davis", True, ""),
        ("oi jarvis", True, ""),
        ("e ai chaves", True, ""),
        ("jarvis abrir calculadora", True, "abrir calculadora"),
        ("chaves abrir calculadora", True, "abrir calculadora"),
        ("já vi como esta a maquina", True, "como esta a maquina"),
        ("ja vi abrir youtube", True, "abrir youtube"),
        ("davis o que eu preciso", True, "o que eu preciso"),
        ("abrir calculadora sem wake", False, ""),
    ],
)
def test_extract_wake_and_command_with_phonetics(
    utterance: str,
    expected_has_wake: bool,
    expected_command: str,
) -> None:
    has_wake, cmd = extract_wake_and_command(utterance)
    assert has_wake == expected_has_wake
    assert cmd == expected_command


@pytest.mark.parametrize("call", ["jarvis", "chaves", "chave", "já vi", "davis", "travis"])
def test_calling_wake_word_alone_replies_and_starts_dialogue(call: str) -> None:
    session = ConversationSession(timeout_seconds=30.0)
    ctx = make_context(session=session)
    corrector = SpeechCorrector()
    ast = Assistant(
        ctx=ctx,
        wake_listener=ctx.listener,
        registry=build_registry(),
        user_name="Ken",
        wake_word="jarvis",
        stop_event=threading.Event(),
        corrector=corrector,
        session=session,
    )

    result = ast.handle_phrase(call)
    assert result is Outcome.CONTINUE
    assert session.is_active() is True
    assert session.is_awaiting_answer() is True

    spoken = ctx.speaker.spoken  # type: ignore[attr-defined]
    assert len(spoken) == 1
    last_spoken = spoken[-1]
    assert any(
        g in last_spoken for g in ("Sim, senhor", "Pois não, senhor", "Às suas ordens, senhor")
    )


def test_speech_corrector_normalizes_two_word_wake_utterances() -> None:
    corrector = SpeechCorrector()
    assert corrector.correct("já vi abrir youtube") == "jarvis abrir youtube"
    assert corrector.correct("ja vi como esta a maquina") == "jarvis como esta a maquina"
    assert corrector.correct("chaves abrir bloco dinota") == "jarvis abrir bloco de notas"
    assert corrector.correct("oi chave abrir calculadora") == "oi jarvis abrir calculadora"


def test_google_speech_listener_adaptive_threshold_bounds() -> None:
    from jarvis.speech.listener import (
        DEFAULT_ENERGY_THRESHOLD,
        MAX_ENERGY_THRESHOLD,
        MIN_ENERGY_THRESHOLD,
        GoogleSpeechListener,
    )
    listener = GoogleSpeechListener("pt-BR")
    # dynamic_energy_threshold deve ser True para adaptação ao piso de ruído do microfone
    assert listener._recognizer.dynamic_energy_threshold is True
    assert listener._recognizer.energy_threshold == DEFAULT_ENERGY_THRESHOLD
    assert listener._recognizer.pause_threshold == 0.65
    assert MIN_ENERGY_THRESHOLD <= listener._recognizer.energy_threshold <= MAX_ENERGY_THRESHOLD
    listener.close()
