"""Gerenciador profundo de processos e tarefas do Windows: finalização de árvores de processos e jogos."""

from __future__ import annotations

import csv
import io
import logging
import subprocess

from jarvis.text_utils import normalize

logger = logging.getLogger(__name__)

APP_EXECUTABLE_ALIASES: dict[str, tuple[str, ...]] = {
    "bloco de notas": ("notepad.exe", "Notepad.exe"),
    "blocos de notas": ("notepad.exe", "Notepad.exe"),
    "notepad": ("notepad.exe", "Notepad.exe"),
    "calculadora": ("calc.exe", "CalculatorApp.exe", "Calculator.exe", "win32calc.exe"),
    "calc": ("calc.exe", "CalculatorApp.exe", "Calculator.exe"),
    "paint": ("mspaint.exe", "PaintStudio.View.exe"),
    "chrome": ("chrome.exe",),
    "google chrome": ("chrome.exe",),
    "navegador": ("chrome.exe", "msedge.exe", "brave.exe", "firefox.exe", "opera.exe"),
    "edge": ("msedge.exe",),
    "microsoft edge": ("msedge.exe",),
    "brave": ("brave.exe",),
    "firefox": ("firefox.exe",),
    "opera": ("opera.exe",),
    "vs code": ("Code.exe", "code.exe"),
    "vscode": ("Code.exe", "code.exe"),
    "visual studio code": ("Code.exe", "code.exe"),
    "cmd": ("cmd.exe",),
    "prompt": ("cmd.exe",),
    "terminal": ("WindowsTerminal.exe", "wt.exe", "cmd.exe"),
    "powershell": ("powershell.exe", "pwsh.exe"),
    "word": ("WINWORD.EXE",),
    "excel": ("EXCEL.EXE",),
    "powerpoint": ("POWERPNT.EXE",),
    "gerenciador de tarefas": ("Taskmgr.exe", "taskmgr.exe"),
    "explorador de arquivos": ("explorer.exe",),
    "configuracoes": ("SystemSettings.exe",),
    "spotify": ("Spotify.exe",),
    "discord": ("Discord.exe", "Update.exe"),
    "whatsapp": ("WhatsApp.exe", "WhatsApp.Root.exe"),
    "telegram": ("Telegram.exe",),
    "steam": ("steam.exe", "steamwebhelper.exe"),
    "epic": ("EpicGamesLauncher.exe",),
    "epic games": ("EpicGamesLauncher.exe",),
    "riot": ("RiotClientServices.exe", "RiotClientUx.exe"),
    "valorant": ("VALORANT-Win64-Shipping.exe", "VALORANT.exe"),
    "fortnite": ("FortniteClient-Win64-Shipping.exe", "FortniteLauncher.exe", "EpicGamesLauncher.exe"),
    "fort": ("FortniteClient-Win64-Shipping.exe", "FortniteLauncher.exe"),
    "counter strike": ("cs2.exe", "csgo.exe"),
    "cs": ("cs2.exe", "csgo.exe"),
    "cs2": ("cs2.exe",),
    "league of legends": ("LeagueClient.exe", "LeagueClientUx.exe", "League of Legends.exe"),
    "lol": ("LeagueClient.exe", "LeagueClientUx.exe", "League of Legends.exe"),
    "roblox": ("RobloxPlayerBeta.exe", "Windows10Universal.exe"),
    "minecraft": ("Minecraft.Windows.exe", "javaw.exe", "MinecraftLauncher.exe"),
    "mine": ("Minecraft.Windows.exe", "javaw.exe", "MinecraftLauncher.exe"),
    "elden ring": ("eldenring.exe",),
    "gta": ("GTA5.exe", "PlayGTAV.exe"),
    "gta 5": ("GTA5.exe", "PlayGTAV.exe"),
    "red dead": ("RDR2.exe",),
    "cyberpunk": ("Cyberpunk2077.exe",),
    "obs": ("obs64.exe", "obs32.exe"),
    "vlc": ("vlc.exe",),
}


class WindowsProcessManager:
    """Acessa profundamente a tabela de tarefas do Windows para encerrar programas e jogos."""

    def list_running(self) -> set[str]:
        """Lê todos os executáveis ativos no Windows através do tasklist."""
        try:
            res = subprocess.run(
                ["tasklist", "/FO", "CSV", "/NH"],
                capture_output=True,
                text=True,
                errors="ignore",
                creationflags=subprocess.CREATE_NO_WINDOW,
                check=False,
            )
            reader = csv.reader(io.StringIO(res.stdout))
            return {row[0].lower() for row in reader if row}
        except OSError as exc:
            logger.error("Falha ao listar processos: %s", exc)
            return set()

    def _find_matching_pids_and_names(self, query: str) -> tuple[list[str], list[str]]:
        """Varre profundamente processos por Nome, Executável e Título da Janela no Windows."""
        clean_q = normalize(query).strip()
        compact_q = clean_q.replace(" ", "")
        exes: list[str] = []
        pids: list[str] = []

        for alias_key, alias_exes in APP_EXECUTABLE_ALIASES.items():
            if clean_q == alias_key or alias_key in clean_q or clean_q in alias_key:
                for e in alias_exes:
                    if e not in exes:
                        exes.append(e)

        try:
            res = subprocess.run(
                ["tasklist", "/V", "/FO", "CSV", "/NH"],
                capture_output=True,
                text=True,
                errors="ignore",
                creationflags=subprocess.CREATE_NO_WINDOW,
                check=False,
            )
            for row in csv.reader(io.StringIO(res.stdout)):
                if len(row) < 2:
                    continue
                img_name = row[0].strip()
                pid = row[1].strip()
                win_title = normalize(row[-1]) if len(row) >= 9 else ""
                img_stem = normalize(img_name.replace(".exe", "")).replace(" ", "")
                if (compact_q and len(compact_q) >= 3 and (compact_q in img_stem or img_stem in compact_q)) or (
                    clean_q and len(clean_q) >= 3 and clean_q in win_title
                ):
                    if img_name.lower() not in ("explorer.exe", "python.exe", "pythonw.exe", "cmd.exe", "svchost.exe"):
                        exes.append(img_name)
                        if pid.isdigit():
                            pids.append(pid)
        except Exception as exc:
            logger.debug("Varredura estendida tasklist /V: %s", exc)

        if not exes and compact_q:
            exes.append(f"{compact_q}.exe")
        return exes, pids

    def close_app(self, name_or_target: str) -> bool:
        """Finaliza a tarefa e toda a árvore de processos (/F /T) no nível do sistema operacional."""
        exes, pids = self._find_matching_pids_and_names(name_or_target)
        closed_any = False

        for exe in exes:
            try:
                res = subprocess.run(
                    ["taskkill", "/F", "/T", "/IM", exe],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    check=False,
                )
                if res.returncode == 0:
                    logger.info("Tarefa finalizada com sucesso (/IM): %s", exe)
                    closed_any = True
            except OSError as exc:
                logger.warning("Erro ao encerrar %s: %s", exe, exc)

        for pid in pids:
            try:
                res = subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", pid],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    check=False,
                )
                if res.returncode == 0:
                    closed_any = True
            except OSError:
                pass

        if not closed_any and name_or_target.strip():
            # Fallback profundo via PowerShell Stop-Process para apps UWP/Store e jogos em segundo plano
            stem = normalize(name_or_target).replace(" ", "")
            try:
                ps_cmd = (
                    f"Get-Process | Where-Object {{ $_.ProcessName -match '{stem}' -or $_.MainWindowTitle -match '{name_or_target}' }} "
                    f"| Where-Object {{ $_.ProcessName -notin @('explorer','python','pythonw') }} "
                    f"| Stop-Process -Force -PassThru"
                )
                res = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", ps_cmd],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=4.0,
                    check=False,
                )
                if res.stdout and res.stdout.strip():
                    closed_any = True
            except Exception:
                pass

        return closed_any
