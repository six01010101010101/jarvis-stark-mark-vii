"""Testes do loop do assistente, utilitários de texto, persistência e configuração."""

from __future__ import annotations

import threading
from datetime import datetime
from pathlib import Path

import pytest

from jarvis import config
from jarvis.assistant import Assistant, greeting_for
from jarvis.commands import Outcome, build_registry
from jarvis.services.message_store import TextFileMessageStore
from jarvis.text_utils import normalize, text_after
from tests.fakes import FakeListener, make_context


def _assistant(ctx, wake: list[str | None]) -> Assistant:  # type: ignore[no-untyped-def]
    return Assistant(
        ctx=ctx, wake_listener=FakeListener(wake), registry=build_registry(), user_name="Tony",
        wake_word="jarvis", stop_event=threading.Event(),
        clock=lambda: datetime(2026, 11, 8, 21, 0), choose=lambda options: options[0],
    )


def test_normalize_and_text_after() -> None:
    assert normalize("  Que Horas  SÃO ") == "que horas sao"
    assert text_after("Jarvis pesquisar Homem de Ferro", "pesquisar") == "Homem de Ferro"
    assert text_after("sem palavra", "pesquisar") == ""


@pytest.mark.parametrize(
    ("hour", "expected"),
    [(2, "Boa noite"), (3, "Boa noite"), (4, "Bom dia"), (8, "Bom dia"), (13, "Boa tarde"), (21, "Boa noite")],
)
def test_greeting_for(hour: int, expected: str) -> None:
    assert greeting_for(hour) == expected


def test_run_introduces_and_stops_on_shutdown() -> None:
    ctx = make_context(["desligar sistema"])
    _assistant(ctx, ["Jarvis"]).run()
    spoken = ctx.speaker.spoken  # type: ignore[attr-defined]
    assert spoken[0].startswith("Boa noite, senhor Tony.")
    assert any(p in s for s in spoken for p in ("Sim, senhor", "Pois não, senhor", "às suas ordens"))
    assert spoken[-1] == "Finalizando todos os sistemas, senhor. Até logo."


def test_inline_command_after_wake_word() -> None:
    ctx = make_context()
    assert _assistant(ctx, []).handle_phrase("Jarvis, abrir calculadora") is Outcome.CONTINUE
    assert ctx.launcher.launched == ["calc.exe"]  # type: ignore[attr-defined]


def test_wake_word_phonetic_variations() -> None:
    for phrase, target in [
        ("Jarbas, abrir calculadora", "calc.exe"),
        ("Iarvis abrir bloco de notas", "notepad.exe"),
        ("Chaves abrir calculadora", "calc.exe"),
        ("Chave abrir paint", "mspaint.exe"),
        ("Já vi abrir calculadora", "calc.exe"),
    ]:
        ctx = make_context()
        _assistant(ctx, []).handle_phrase(phrase)
        assert ctx.launcher.launched == [target]  # type: ignore[attr-defined]


def test_compound_commands_execution() -> None:
    ctx = make_context()
    _assistant(ctx, []).handle_phrase("Jarvis, abrir bloco de notas e calculadora")
    assert ctx.launcher.launched == ["notepad.exe", "calc.exe"]  # type: ignore[attr-defined]


def test_assistant_autocorrects_phonetic_distortions() -> None:
    from jarvis.services.speech_corrector import SpeechCorrector
    ctx = make_context()
    corrector = SpeechCorrector()
    ast = Assistant(
        ctx=ctx,
        wake_listener=ctx.listener,
        registry=build_registry(),
        user_name="Ken",
        wake_word="jarvis",
        stop_event=threading.Event(),
        corrector=corrector,
    )
    # Usuário fala "chave abrir bloco dinota"
    # O corretor transforma em "jarvis abrir bloco de notas" e executa!
    assert ast.handle_phrase("chave abrir bloco dinota") is Outcome.CONTINUE
    assert ctx.launcher.launched == ["notepad.exe"]  # type: ignore[attr-defined]


def test_phrase_without_wake_word_also_executes() -> None:
    ctx = make_context()
    _assistant(ctx, []).handle_phrase("abrir calculadora")
    assert ctx.launcher.launched == ["calc.exe"]  # type: ignore[attr-defined]


def test_message_store_appends_utf8(tmp_path: Path) -> None:
    store = TextFileMessageStore(tmp_path / "msgs.txt", clock=lambda: datetime(2026, 1, 2, 3, 4, 5))
    store.save("reunião às 10h")
    assert (tmp_path / "msgs.txt").read_text(encoding="utf-8") == "02/01/2026 03:04:05 - reunião às 10h\n"
    with pytest.raises(ValueError):
        store.save("   ")


def test_load_settings_requires_api_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("JARVIS_USER_NAME", "Tony")
    with pytest.raises(config.ConfigError):
        config.load_settings(tmp_path / "inexistente.env")


def test_load_settings_reads_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("GEMINI_API_KEY", "JARVIS_USER_NAME", "GEMINI_MODEL", "JARVIS_TRANSCRIPTION_FILE"):
        monkeypatch.delenv(name, raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("GEMINI_API_KEY=abc\nJARVIS_USER_NAME=Tony\n", encoding="utf-8")
    settings = config.load_settings(env_file)
    assert settings.gemini_api_key == "abc"
    assert settings.gemini_model == config.DEFAULT_GEMINI_MODEL
    assert settings.transcription_file.name == config.TRANSCRIPTION_FILENAME


def test_continuous_dialogue_without_repeating_wake_word() -> None:
    from jarvis.services.conversation_session import ConversationSession

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

    # Inicia diálogo chamando Jarvis
    ast.handle_phrase("jarvis")
    assert session.is_active() is True

    # Próxima frase executa diretamente sem precisar repetir 'Jarvis'
    assert ast.handle_phrase("abrir bloco de notas") is Outcome.CONTINUE
    assert ctx.launcher.launched == ["notepad.exe"]  # type: ignore[attr-defined]


def test_closing_phrase_ends_dialogue_session() -> None:
    from jarvis.services.conversation_session import ConversationSession

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

    assert ast.handle_phrase("valeu jarvis") is Outcome.CONTINUE
    assert session.is_active() is False
    spoken = ctx.speaker.spoken  # type: ignore[attr-defined]
    assert spoken[-1] == "Às suas ordens, senhor. Conversa encerrada."
