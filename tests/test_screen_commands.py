"""Testes unitários dos comandos de inspeção e captura de tela."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from jarvis.commands.registry import CommandContext, Outcome
from jarvis.commands.screen_commands import screen_commands
from jarvis.services.screen_inspector import ScreenInfo, ScreenInspector


def _build_context() -> tuple[CommandContext, MagicMock]:
    speaker = MagicMock()
    listener = MagicMock()
    view = MagicMock()
    answers = MagicMock()
    messages = MagicMock()
    launcher = MagicMock()
    processes = MagicMock()

    ctx = CommandContext(
        speaker=speaker,
        listener=listener,
        view=view,
        answers=answers,
        messages=messages,
        launcher=launcher,
        processes=processes,
    )
    return ctx, speaker


def test_screen_inspect_command() -> None:
    inspector = MagicMock(spec=ScreenInspector)
    inspector.inspect.return_value = ScreenInfo(
        window_title="VS Code - Jarvis Project",
        width=1920,
        height=1080,
        screenshot_path=None,
    )

    cmds = {cmd.name: cmd for cmd in screen_commands(inspector=inspector)}
    ctx, speaker = _build_context()

    outcome = cmds["screen_inspect"].handler(ctx, "o que está na minha tela")

    assert outcome is Outcome.CONTINUE
    inspector.inspect.assert_called_once_with(take_screenshot=False)
    speech = speaker.say.call_args[0][0]
    assert "VS Code - Jarvis Project" in speech
    assert "1920x1080" in speech


def test_screen_capture_command() -> None:
    temp_shot = Path("screenshot_sample.png")
    inspector = MagicMock(spec=ScreenInspector)
    inspector.inspect.return_value = ScreenInfo(
        window_title="Desktop",
        width=2560,
        height=1440,
        screenshot_path=temp_shot,
    )

    cmds = {cmd.name: cmd for cmd in screen_commands(inspector=inspector)}
    ctx, speaker = _build_context()

    outcome = cmds["screen_capture"].handler(ctx, "tirar print")

    assert outcome is Outcome.CONTINUE
    inspector.inspect.assert_called_once_with(take_screenshot=True)
    assert speaker.say.called
