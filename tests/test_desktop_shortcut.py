"""Testes unitários da criação do inicializador unificado e atalho na Área de Trabalho."""

from __future__ import annotations

from pathlib import Path
from jarvis.services.desktop_shortcut import PROJECT_ROOT, LAUNCHER_BAT


def test_launcher_bat_points_to_unified_script() -> None:
    assert LAUNCHER_BAT.name == "INICIAR_JARVIS.bat"
    assert (PROJECT_ROOT / "INICIAR_JARVIS.bat").exists()
