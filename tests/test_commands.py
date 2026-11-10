"""Testes do registro e dos comandos de voz."""

from __future__ import annotations

from datetime import datetime

import pytest

from jarvis.commands import Outcome, build_registry
from jarvis.commands.info_commands import info_commands
from jarvis.commands.registry import CommandRegistry
from jarvis.services.launcher import resolve_app_target
from tests.fakes import FakeAnswers, FakeLauncher, FakeMessages, make_context


def test_resolve_app_target_friendly_names() -> None:
    assert resolve_app_target("bloco de notas") == "notepad.exe"
    assert resolve_app_target("calculadora") == "calc.exe"
    assert resolve_app_target("google chrome") == "chrome.exe"
    assert "fortnite" in str(resolve_app_target("fort")).lower()
    assert resolve_app_target("app_totalmente_inexistente_999") is None


@pytest.mark.parametrize(
    ("utterance", "target"),
    [
        ("Abrir calculadora", "calc.exe"),
        ("abrir Paint", "mspaint.exe"),
        ("abrir bloco de notas", "notepad.exe"),
        ("abrir blocos de notas", "notepad.exe"),
        ("abrir excel", "excel.exe"),
        ("Abrir Word", "winword.exe"),
        ("abrir cmd", "cmd.exe"),
        ("abrir VS Code", "code"),
        ("consertar internet", "ms-settings:troubleshoot"),
        ("Concertar internet", "ms-settings:troubleshoot"),
    ],
)
def test_program_commands_launch_expected_target(utterance: str, target: str) -> None:
    ctx = make_context()
    assert build_registry().dispatch(ctx, utterance) is Outcome.CONTINUE
    assert ctx.launcher.launched == [target]  # type: ignore[attr-defined]


def test_close_app_calls_process_manager() -> None:
    ctx = make_context()
    build_registry().dispatch(ctx, "fechar bloco de notas")
    assert ctx.processes.closed == ["bloco de notas"]  # type: ignore[attr-defined]
    assert "fechando" in ctx.speaker.spoken[-1].lower()  # type: ignore[attr-defined]


def test_open_youtube_home() -> None:
    ctx = make_context()
    build_registry().dispatch(ctx, "abrir youtube")
    assert ctx.launcher.urls == ["https://www.youtube.com"]  # type: ignore[attr-defined]


def test_open_social_media() -> None:
    ctx = make_context()
    build_registry().dispatch(ctx, "abrir instagram")
    assert ctx.launcher.urls == ["https://www.instagram.com"]  # type: ignore[attr-defined]


def test_whatsapp_with_phone_and_message() -> None:
    ctx = make_context()
    build_registry().dispatch(ctx, "mandar mensagem no whatsapp para 11999998888 dizendo reuniao confirmada")
    assert any("web.whatsapp.com/send?phone=5511999998888" in url for url in ctx.launcher.urls)  # type: ignore[attr-defined]


def test_open_browser_uses_default_browser() -> None:
    ctx = make_context()
    build_registry().dispatch(ctx, "abrir navegador")
    assert ctx.launcher.urls == ["https://www.google.com"]  # type: ignore[attr-defined]


def test_launch_failure_is_reported_by_voice() -> None:
    ctx = make_context(launcher=FakeLauncher(fail=True))
    assert build_registry().dispatch(ctx, "abrir excel") is Outcome.CONTINUE
    assert "não foi possível" in ctx.speaker.spoken[-1].lower()  # type: ignore[attr-defined]


def test_search_with_inline_topic_asks_ai() -> None:
    answers = FakeAnswers(reply="Paris, senhor.")
    ctx = make_context(answers=answers)
    build_registry().dispatch(ctx, "pesquisar capital da França")
    assert answers.questions == ["capital da França"]
    assert ctx.speaker.spoken[-1] == "Paris, senhor."  # type: ignore[attr-defined]


def test_play_music_opens_youtube_search() -> None:
    ctx = make_context(["Back in Black"])
    build_registry().dispatch(ctx, "tocar música")
    assert ctx.launcher.urls == [  # type: ignore[attr-defined]
        "https://www.youtube.com/results?search_query=Back+in+Black"
    ]


def test_transcribe_saves_message() -> None:
    messages = FakeMessages()
    ctx = make_context(["comprar leite"], messages=messages)
    build_registry().dispatch(ctx, "transcrever")
    assert messages.saved == ["comprar leite"]


def test_open_site_formats_url() -> None:
    ctx = make_context()
    build_registry().dispatch(ctx, "abrir site github")
    assert ctx.launcher.urls == ["https://www.github.com"]  # type: ignore[attr-defined]


def test_conversational_phrase_routes_to_ai() -> None:
    ctx = make_context(answers=FakeAnswers(reply="Tudo em ordem, senhor."))
    assert build_registry().dispatch(ctx, "como você está hoje") is Outcome.CONTINUE
    assert ctx.speaker.spoken[-1] == "Tudo em ordem, senhor."  # type: ignore[attr-defined]


def test_theme_playlists_dispatch() -> None:
    ctx = make_context()
    build_registry().dispatch(ctx, "playlist de foco")
    assert any("lofi" in url for url in ctx.launcher.urls)  # type: ignore[attr-defined]

