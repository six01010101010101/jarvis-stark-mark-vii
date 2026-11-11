"""Abertura segura e resolução inteligente de programas, jogos e URLs no Windows."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import webbrowser
from pathlib import Path

from jarvis.contracts import LaunchError
from jarvis.services.app_indexer import PcAppIndexer
from jarvis.text_utils import normalize

logger = logging.getLogger(__name__)

_ALLOWED_URL_SCHEMES = ("http://", "https://")
_CREATION_FLAGS = getattr(subprocess, "CREATE_NO_WINDOW", 0)

COMMON_APP_MAP: dict[str, str] = {
    "bloco de notas": "notepad.exe",
    "blocos de notas": "notepad.exe",
    "notepad": "notepad.exe",
    "calculadora": "calc.exe",
    "calc": "calc.exe",
    "paint": "mspaint.exe",
    "mspaint": "mspaint.exe",
    "chrome": "chrome.exe",
    "google chrome": "chrome.exe",
    "navegador": "https://www.google.com",
    "edge": "msedge.exe",
    "microsoft edge": "msedge.exe",
    "brave": "brave.exe",
    "firefox": "firefox.exe",
    "opera": "opera.exe",
    "vs code": "code",
    "vscode": "code",
    "visual studio code": "code",
    "cmd": "cmd.exe",
    "prompt": "cmd.exe",
    "terminal": "wt.exe",
    "powershell": "powershell.exe",
    "excel": "excel.exe",
    "word": "winword.exe",
    "powerpoint": "powerpnt.exe",
    "gerenciador de tarefas": "taskmgr.exe",
    "task manager": "taskmgr.exe",
    "explorador de arquivos": "explorer.exe",
    "meus arquivos": "explorer.exe",
    "configuracoes": "ms-settings:",
    "painel de controle": "control.exe",
    "downloads": str(Path.home() / "Downloads"),
    "steam": "steam://open/main",
    "spotify": "spotify:",
    "discord": "discord:",
    "whatsapp": "whatsapp:",
}

_APP_INDEXER = PcAppIndexer()


def _find_windows_store_app_id(query: str) -> str | None:
    """Procura aplicativos e jogos UWP/Microsoft Store/Xbox via Get-StartApps."""
    if os.name != "nt":
        return None
    clean = normalize(query).strip()
    if len(clean) < 3:
        return None
    try:
        ps_cmd = (
            f"Get-StartApps | Where-Object {{ $_.Name -like '*{clean}*' }} "
            "| Select-Object -First 1 -ExpandProperty AppID"
        )
        res = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            capture_output=True,
            text=True,
            timeout=2.5,
            creationflags=_CREATION_FLAGS,
        )
        app_id = (res.stdout or "").strip()
        if app_id:
            return f"shell:AppsFolder\\{app_id}"
    except Exception:
        pass
    return None


def resolve_app_target(target: str) -> str | None:
    """Resolve nomes amigáveis ou abreviações em executáveis, jogos ou atalhos instalados."""
    norm = normalize(target)
    if norm in COMMON_APP_MAP:
        # Se for protocolo (steam:, discord:, spotify:), prefere atalho local se existir
        mapped = COMMON_APP_MAP[norm]
        if mapped.endswith(":"):
            indexed = _APP_INDEXER.find_app(target)
            if indexed:
                return indexed
        return mapped

    # 1. Verifica no indexador global de jogos e programas do computador
    indexed_path = _APP_INDEXER.find_app(target)
    if indexed_path:
        return indexed_path

    # 2. Verifica executáveis no PATH do sistema
    if shutil.which(target):
        return target
    if not target.endswith(".exe") and shutil.which(f"{target}.exe"):
        return f"{target}.exe"

    # 3. Aceita caminhos diretos ou URIs registradas
    if target.endswith((".exe", ".msc", ".bat", ".cmd", ".lnk", ".url")) or ":" in target:
        return target

    # 4. Fallback em Apps/Jogos do Windows (Get-StartApps / Xbox / Store)
    store_uri = _find_windows_store_app_id(target)
    if store_uri:
        return store_uri

    return None


class WindowsLauncher:
    """Abre programas, jogos e URLs com proteção total contra caixas de erro do Windows."""

    def launch(self, target: str) -> None:
        """Abre o aplicativo ou jogo de forma assíncrona."""
        if not target or any(ch in target for ch in '&|<>^"'):
            raise LaunchError(f"Alvo inválido: {target!r}")

        resolved = resolve_app_target(target)
        if not resolved:
            raise LaunchError(f"Aplicativo ou jogo não encontrado no sistema: {target}")

        if resolved.startswith(_ALLOWED_URL_SCHEMES):
            self.open_url(resolved)
            return

        try:
            subprocess.Popen(
                ["cmd.exe", "/c", "start", "", resolved],
                creationflags=_CREATION_FLAGS,
            )
        except OSError as exc:
            raise LaunchError(f"Não foi possível iniciar {target}: {exc}") from exc

    def open_url(self, url: str) -> None:
        """Abre a URL no navegador padrão."""
        if not url.startswith(_ALLOWED_URL_SCHEMES):
            raise LaunchError(f"URL não permitida: {url}")
        if not webbrowser.open(url):
            raise LaunchError(f"Não foi possível abrir o navegador para {url}")
