"""Testes unitários para controles nativos de volume, multimídia e print screen."""

from __future__ import annotations

import pytest

from jarvis.commands.multimedia_control_commands import multimedia_control_commands
from jarvis.commands.registry import Outcome
from tests.fakes import make_context


def test_volume_and_media_commands_matching() -> None:
    cmds = {c.name: c for c in multimedia_control_commands()}

    # Volume
    assert cmds["volume_up"].matches("aumentar volume")
    assert cmds["volume_up"].matches("aumenta o som")
    assert cmds["volume_down"].matches("diminuir volume")
    assert cmds["volume_mute"].matches("mutar som")

    # Mídia
    assert cmds["media_play_pause"].matches("pausar musica")
    assert cmds["media_play_pause"].matches("pausar video")
    assert cmds["media_next"].matches("proxima musica")
    assert cmds["media_prev"].matches("musica anterior")

    # Screenshot
    assert cmds["screenshot"].matches("tirar print")
    assert cmds["screenshot"].matches("capturar tela")


def test_multimedia_commands_execution_returns_continue() -> None:
    ctx = make_context()
    for cmd in multimedia_control_commands():
        res = cmd.handler(ctx, cmd.triggers[0])
        assert res is Outcome.CONTINUE
