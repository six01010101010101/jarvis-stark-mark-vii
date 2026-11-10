"""Testes unitários do subsistema de ponte e visibilidade do terminal (TerminalBridge)."""

from __future__ import annotations

import io
from unittest.mock import patch

from jarvis.services.terminal_bridge import TerminalBridge


def test_terminal_bridge_disabled_starts_no_thread() -> None:
    bridge = TerminalBridge(enabled=False)
    assert bridge.get_input() is None
    bridge.close()


def test_terminal_bridge_queue_and_get_input() -> None:
    bridge = TerminalBridge(enabled=False)
    bridge._queue.put("jarvis abrir calculadora")
    assert bridge.get_input() == "jarvis abrir calculadora"
    assert bridge.get_input() is None
    bridge.close()


def test_terminal_bridge_hud_and_notifications_output() -> None:
    bridge = TerminalBridge(enabled=True)
    captured = io.StringIO()
    with patch("sys.stdout", captured):
        bridge.print_hud_banner("Microfone Teste", 44100)
        bridge.notify_capturing()
        bridge.notify_transcription("jarvis")
        bridge.notify_wake("jarvis")
        bridge.notify_reply("Sim, senhor Ken?")

    out = captured.getvalue()
    assert "CONECTIVIDADE DA PORTA" in out
    assert "Microfone Teste" in out
    assert "TRANSCRIÇÃO OBTIDA" in out
    assert "jarvis" in out
    assert "Sim, senhor Ken?" in out
    bridge.close()
