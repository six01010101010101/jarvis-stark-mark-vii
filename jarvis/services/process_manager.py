"""Gerenciador de processos do Windows: monitoramento em tempo real e encerramento de programas."""

from __future__ import annotations

import csv
import io
import logging
import subprocess

from jarvis.text_utils import normalize

logger = logging.getLogger(__name__)

APP_EXECUTABLE_ALIASES: dict[str, tuple[str, ...]] = {
    "bloco de notas": ("notepad.exe",),
    "blocos de notas": ("notepad.exe",),
    "notepad": ("notepad.exe",),
    "calculadora": ("calc.exe", "CalculatorApp.exe", "Calculator.exe"),
    "paint": ("mspaint.exe", "PaintStudio.View.exe"),
    "chrome": ("chrome.exe",),
    "google chrome": ("chrome.exe",),
    "navegador": ("chrome.exe", "msedge.exe"),
    "edge": ("msedge.exe",),
    "vs code": ("code.exe",),
    "vscode": ("code.exe",),
    "visual studio code": ("code.exe",),
    "cmd": ("cmd.exe",),
    "prompt": ("cmd.exe",),
    "powershell": ("powershell.exe",),
    "word": ("WINWORD.EXE",),
    "excel": ("EXCEL.EXE",),
    "gerenciador de tarefas": ("taskmgr.exe",),
    "spotify": ("Spotify.exe",),
    "discord": ("Discord.exe",),
    "whatsapp": ("WhatsApp.exe",),
    "steam": ("steam.exe",),
    "fortnite": ("FortniteClient-Win64-Shipping.exe", "FortniteLauncher.exe"),
    "fort": ("FortniteClient-Win64-Shipping.exe", "FortniteLauncher.exe"),
    "counter strike": ("cs2.exe",),
    "cs": ("cs2.exe",),
    "league of legends": ("LeagueClient.exe",),
    "lol": ("LeagueClient.exe",),
    "roblox": ("RobloxPlayerBeta.exe",),
    "elden ring": ("eldenring.exe",),
    "gta": ("GTA5.exe",),
}


class WindowsProcessManager:
    """Implementa o controle de processos do Windows em tempo real."""

    def list_running(self) -> set[str]:
        """Lê todos os executáveis ativos no Windows através do tasklist."""
        try:
            res = subprocess.run(
                ["tasklist", "/FO", "CSV", "/NH"],
                capture_output=True,
                text=True,
                errors="ignore",
                check=False,
            )
            reader = csv.reader(io.StringIO(res.stdout))
            return {row[0].lower() for row in reader if row}
        except OSError as exc:
            logger.error("Falha ao listar processos: %s", exc)
            return set()

    def close_app(self, name_or_target: str) -> bool:
        """Encerra um aplicativo pelo nome amigável ou nome do processo."""
        clean_name = normalize(name_or_target).strip()
        candidates: list[str] = list(APP_EXECUTABLE_ALIASES.get(clean_name, ()))

        if not candidates:
            # Tenta encontrar correspondência entre os processos ativos no sistema
            running = self.list_running()
            target_key = clean_name.replace(" ", "")
            matched = [exe for exe in running if target_key in exe.replace(".exe", "")]
            candidates.extend(matched)

        if not candidates:
            # Tentativa direta com extensão .exe
            candidates.append(f"{clean_name.replace(' ', '')}.exe")

        closed_any = False
        for exe in candidates:
            try:
                res = subprocess.run(
                    ["taskkill", "/F", "/T", "/IM", exe],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if res.returncode == 0:
                    logger.info("Processo encerrado com sucesso: %s", exe)
                    closed_any = True
            except OSError as exc:
                logger.warning("Erro ao tentar encerrar %s: %s", exe, exc)

        return closed_any
