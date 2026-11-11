"""Testes das ferramentas avançadas inspiradas no OpenJarvis (SO, YouTube, Web e Retomada)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from jarvis.commands import CommandContext, build_registry
from jarvis.services.browser_controller import BrowserAndMediaController
from jarvis.services.conversation_session import ConversationSession
from jarvis.services.semantic_intent_adapter import SemanticIntentAdapter
from jarvis.services.web_search_engine import WebSearchEngine
from jarvis.services.windows_automation import WindowsExplorerAutomation


def test_windows_explorer_resolution():
    auto = WindowsExplorerAutomation()
    assert auto._resolve_path("downloads") == Path.home() / "Downloads"
    assert auto._resolve_path("desktop") == Path.home() / "Desktop"
    assert auto._resolve_path("c") == Path("C:\\")


@patch("subprocess.Popen")
def test_windows_explorer_open_and_select(mock_popen):
    auto = WindowsExplorerAutomation()
    assert auto.open_folder("downloads") is True
    mock_popen.assert_called_with(["explorer.exe", str(Path.home() / "Downloads")], shell=False)

    fake_file = Path.home() / "Downloads" / "test_dummy.txt"
    with patch.object(Path, "exists", return_value=True):
        assert auto.select_file_in_explorer(fake_file) is True
        mock_popen.assert_called_with(["explorer.exe", f"/select,{fake_file.resolve()}"], shell=False)


@patch("subprocess.Popen")
@patch("ctypes.windll.user32.keybd_event")
def test_browser_and_media_controller(mock_keybd, mock_popen):
    controller = BrowserAndMediaController()
    assert controller.play_youtube_search("Iron Man AC DC") is True
    assert mock_popen.called

    assert controller.toggle_play_pause() is True
    assert mock_keybd.call_count >= 2


def test_web_search_engine():
    engine = WebSearchEngine(timeout=3.0)
    # Testa busca estruturada
    results = engine.search("Albert Einstein", max_results=2)
    assert isinstance(results, list)
    if results:
        assert "title" in results[0]
        assert "snippet" in results[0]
        assert "url" in results[0]

    prompt_block = engine.format_search_for_prompt("Albert Einstein")
    if results:
        assert "[PESQUISA EM TEMPO REAL" in prompt_block


def test_semantic_intent_adapter():
    yt1 = SemanticIntentAdapter.parse_colloquial_action("poe no yt musica relaxante")
    assert yt1 == {"action": "play_youtube", "target": "musica relaxante"}

    yt2 = SemanticIntentAdapter.parse_colloquial_action("solta o som do ac dc")
    assert yt2 == {"action": "play_youtube", "target": "ac dc"}

    sel = SemanticIntentAdapter.parse_colloquial_action("destaca o arquivo relatorio.pdf")
    assert sel is not None
    assert sel["action"] == "select_file"
    assert "relatorio" in sel["target"]

    pause = SemanticIntentAdapter.parse_colloquial_action("pausa o video ai")
    assert pause == {"action": "toggle_media_pause", "target": ""}

    resume = SemanticIntentAdapter.parse_colloquial_action("retome a conversa")
    assert resume == {"action": "resume_speech", "target": ""}


def test_stop_and_resume_dialogue_flow():
    registry = build_registry()
    session = ConversationSession()
    mock_speaker = MagicMock()
    ctx = CommandContext(
        speaker=mock_speaker, listener=MagicMock(), view=MagicMock(), answers=MagicMock(),
        messages=MagicMock(), launcher=MagicMock(), processes=MagicMock(), session=session,
    )

    # 1. Simula interrupção e gravação da fala
    session.set_interrupted_speech("Estávamos analisando os parâmetros quânticos da armadura Mark VII.")
    stop_cmd = registry.find("pare jarvis")
    assert stop_cmd is not None
    stop_cmd.handler(ctx, "pare jarvis")
    mock_speaker.stop.assert_called_once()

    # 2. Simula pedido de retomada de conversa
    resume_cmd = registry.find("retome a conversa")
    assert resume_cmd is not None
    resume_cmd.handler(ctx, "retome a conversa")

    mock_speaker.say.assert_called_once()
    assert "Estávamos analisando os parâmetros quânticos" in mock_speaker.say.call_args[0][0]


@patch("subprocess.Popen")
@patch("ctypes.windll.user32.keybd_event")
def test_automation_commands_via_registry(mock_keybd, mock_popen):
    registry = build_registry()
    mock_speaker = MagicMock()
    ctx = CommandContext(
        speaker=mock_speaker, listener=MagicMock(), view=MagicMock(), answers=MagicMock(),
        messages=MagicMock(), launcher=MagicMock(), processes=MagicMock(),
    )

    cmd_yt = registry.find("tocar no youtube imagine dragons")
    assert cmd_yt is not None
    cmd_yt.handler(ctx, "tocar no youtube imagine dragons")
    mock_speaker.say.assert_called()

    cmd_pause = registry.find("pausar video")
    assert cmd_pause is not None
    cmd_pause.handler(ctx, "pausar video")
    assert mock_keybd.called
