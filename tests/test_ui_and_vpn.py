"""Testes dos recursos de VPN Proton, temas da HUD, holograma e execução sequencial."""

from __future__ import annotations

import tkinter as tk
from unittest.mock import MagicMock, patch
import pytest

from jarvis.commands import CommandContext, build_registry
from jarvis.services.proton_vpn import ProtonVPNManager
from jarvis.ui.theme import DARK_THEME, LIGHT_THEME, get_theme_palette


def test_theme_palettes():
    dark = get_theme_palette("dark")
    assert dark["bg"] == DARK_THEME["bg"]
    assert dark["fg"] == DARK_THEME["fg"]

    light = get_theme_palette("light")
    assert light["bg"] == LIGHT_THEME["bg"]
    assert light["fg"] == LIGHT_THEME["fg"]


@patch("subprocess.Popen")
def test_proton_vpn_manager_launch(mock_popen):
    vpn = ProtonVPNManager()
    with patch.object(vpn, "is_installed", return_value=True), patch.object(vpn, "_exe_path", "C:\\fake\\ProtonVPN.exe"):
        assert vpn.launch_client() is True
        mock_popen.assert_called_with(["C:\\fake\\ProtonVPN.exe"], shell=False)


@patch("subprocess.run")
def test_proton_vpn_manager_disconnect(mock_run):
    vpn = ProtonVPNManager()
    assert vpn.disconnect() is True
    assert mock_run.called


def test_vpn_voice_commands():
    registry = build_registry()
    cmd_connect = registry.find("ativar vpn")
    assert cmd_connect is not None

    mock_speaker = MagicMock()
    ctx = CommandContext(
        speaker=mock_speaker, listener=MagicMock(), view=MagicMock(), answers=MagicMock(),
        messages=MagicMock(), launcher=MagicMock(), processes=MagicMock(),
    )

    with patch.object(ProtonVPNManager, "is_installed", return_value=True), patch.object(ProtonVPNManager, "launch_client", return_value=True):
        cmd_connect.handler(ctx, "ativar vpn")
        mock_speaker.say.assert_called_once()
        assert "Proton VPN" in mock_speaker.say.call_args[0][0]

    cmd_status = registry.find("status da vpn")
    assert cmd_status is not None
    with patch.object(ProtonVPNManager, "get_public_ip_info", return_value={"ip": "185.159.157.1", "country": "CH"}):
        cmd_status.handler(ctx, "status da vpn")
        assert "185.159.157.1" in mock_speaker.say.call_args[0][0]


@patch("subprocess.Popen")
def test_sequential_execution_speaks_first(mock_popen):
    """Garante que a confirmação por voz ocorre antes do disparo da ação física."""
    events = []
    mock_speaker = MagicMock()
    mock_speaker.say.side_effect = lambda text: events.append(f"SPEAK: {text}")
    mock_popen.side_effect = lambda *args, **kwargs: events.append("POPEN_LAUNCHED")

    ctx = CommandContext(
        speaker=mock_speaker, listener=MagicMock(), view=MagicMock(), answers=MagicMock(),
        messages=MagicMock(), launcher=MagicMock(), processes=MagicMock(),
    )

    registry = build_registry()
    cmd_folder = registry.find("abrir pasta downloads")
    assert cmd_folder is not None
    cmd_folder.handler(ctx, "abrir pasta downloads")

    # Verifica que o evento SPEAK ocorreu estritamente antes do POPEN_LAUNCHED
    assert len(events) >= 2
    assert events[0].startswith("SPEAK:")
    assert events[1] == "POPEN_LAUNCHED"


def test_hologram_mask_canvas():
    root = tk.Tk()
    root.withdraw()
    try:
        from jarvis.ui.stark_hologram import StarkHologramMask
        mask = StarkHologramMask(root, size=50)
        assert mask._size == 50
        mask.set_palette(glow="#00FFFF", bg="#000000")
        assert len(mask.find_all()) > 0
    finally:
        root.destroy()
