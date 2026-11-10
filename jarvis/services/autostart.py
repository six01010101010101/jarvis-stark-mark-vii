"""Gerenciamento de inicialização automática do J.A.R.V.I.S. com o Windows."""

from __future__ import annotations

import logging
import sys
import winreg
from pathlib import Path

logger = logging.getLogger(__name__)

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "JarvisAssistant"


def get_startup_command() -> str:
    """Calcula o comando para inicializar o Jarvis em segundo plano no login do Windows."""
    venv_python = Path(sys.prefix) / "Scripts" / "pythonw.exe"
    if not venv_python.exists():
        venv_python = Path(sys.executable)

    # Executa o módulo jarvis nativamente
    return f'"{venv_python}" -m jarvis'


def is_autostart_enabled() -> bool:
    """Verifica se o Jarvis já está configurado no registro para iniciar com o Windows."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_READ) as key:
            winreg.QueryValueEx(key, APP_NAME)
            return True
    except OSError:
        return False


def enable_autostart() -> bool:
    """Registra o Jarvis para iniciar automaticamente sempre que o computador for ligado."""
    command = get_startup_command()
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, command)
        logger.info("J.A.R.V.I.S. configurado para iniciar automaticamente com o Windows: %s", command)
        return True
    except OSError as exc:
        logger.warning("Falha ao registrar inicialização automática no Windows: %s", exc)
        return False


def disable_autostart() -> bool:
    """Remove a inicialização automática do Windows."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, APP_NAME)
        return True
    except OSError:
        return False
