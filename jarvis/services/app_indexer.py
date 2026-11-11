"""Indexador profundo de aplicativos, jogos (Steam, Epic, Riot, Roblox) e Registro do Windows."""

from __future__ import annotations

import logging
import os
from pathlib import Path
import winreg

from jarvis.text_utils import normalize

logger = logging.getLogger(__name__)

SEARCH_DIRECTORIES = (
    Path.home() / "OneDrive" / "Área de Trabalho",
    Path.home() / "OneDrive" / "Desktop",
    Path.home() / "Desktop",
    Path(r"C:\Users\Public\Desktop"),
    Path(r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs"),
    Path.home() / r"AppData\Roaming\Microsoft\Windows\Start Menu\Programs",
)

GAME_AND_APP_DIRS = (
    Path(r"C:\Program Files (x86)\Steam\steamapps\common"),
    Path(r"C:\Program Files\Steam\steamapps\common"),
    Path(r"C:\Program Files\Epic Games"),
    Path(r"C:\Riot Games"),
    Path.home() / r"AppData\Local\Programs",
    Path.home() / r"AppData\Local\Discord",
    Path.home() / r"AppData\Roaming\Spotify",
)

POPULAR_ALIASES: dict[str, str] = {
    "fort": "fortnite",
    "fortn": "fortnite",
    "fortnite": "fortnite",
    "vava": "valorant",
    "valorant": "valorant",
    "cs": "counter strike",
    "cs2": "counter strike",
    "counter": "counter strike",
    "lol": "league of legends",
    "league": "league of legends",
    "gta": "grand theft auto",
    "gta5": "grand theft auto",
    "gtav": "grand theft auto",
    "elden": "elden ring",
    "roblox": "roblox player",
    "mine": "minecraft",
    "minecraft": "minecraft",
    "steam": "steam",
    "epic": "epic games launcher",
    "epic games": "epic games launcher",
    "riot": "riot client",
    "discord": "discord",
    "disc": "discord",
    "spotify": "spotify",
    "spot": "spotify",
    "obs": "obs studio",
    "vlc": "vlc media player",
    "bloco": "bloco de notas",
    "blocos": "bloco de notas",
    "calc": "calculadora",
    "zap": "whatsapp",
    "wpp": "whatsapp",
    "insta": "instagram",
    "face": "facebook",
    "yt": "youtube",
}


class PcAppIndexer:
    """Escaneia e mapeia todos os jogos, executáveis, Registro do Windows e atalhos da máquina."""

    def __init__(self) -> None:
        self._index: dict[str, str] = {}
        self.refresh()

    def _scan_registry_app_paths(self, index: dict[str, str]) -> None:
        """Lê executáveis registrados no Windows Registry (App Paths)."""
        reg_KeyPath = r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"
        for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            try:
                with winreg.OpenKey(root, reg_KeyPath) as base_key:
                    sub_count = winreg.QueryInfoKey(base_key)[0]
                    for i in range(sub_count):
                        sub_name = winreg.EnumKey(base_key, i)
                        with winreg.OpenKey(base_key, sub_name) as sub_key:
                            val, _ = winreg.QueryValueEx(sub_key, "")
                            if isinstance(val, str) and val.strip():
                                exe_path = val.strip().strip('"')
                                stem = normalize(Path(sub_name).stem)
                                if stem and Path(exe_path).exists():
                                    index.setdefault(stem, exe_path)
            except OSError:
                continue

    def _scan_game_folders(self, index: dict[str, str]) -> None:
        """Indexa jogos instalados na Steam, Epic Games, Riot e AppData."""
        for base_dir in GAME_AND_APP_DIRS:
            if not base_dir.exists():
                continue
            try:
                for sub in base_dir.iterdir():
                    if not sub.is_dir():
                        continue
                    folder_key = normalize(sub.name)
                    for exe in sub.glob("*.exe"):
                        name_low = exe.stem.lower()
                        if any(skip in name_low for skip in ("unins", "crash", "setup", "update", "redist", "dxsetup")):
                            continue
                        index.setdefault(folder_key, str(exe))
                        index.setdefault(normalize(exe.stem), str(exe))
            except OSError:
                continue

    def refresh(self) -> None:
        """Atualiza o mapa de atalhos, jogos e executáveis instalados no Windows."""
        new_index: dict[str, str] = {}
        for directory in SEARCH_DIRECTORIES:
            if not directory.exists():
                continue
            try:
                for file_path in directory.rglob("*"):
                    if file_path.suffix.lower() in (".lnk", ".url"):
                        clean_name = normalize(file_path.stem)
                        new_index[clean_name] = str(file_path)
            except OSError as exc:
                logger.warning("Erro ao escanear %s: %s", directory, exc)

        if os.name == "nt":
            self._scan_registry_app_paths(new_index)
            self._scan_game_folders(new_index)

        self._index = new_index
        logger.info("Indexador de apps carregado: %d itens indexados.", len(self._index))

    def get_known_app_names(self, limit: int = 50) -> list[str]:
        """Retorna uma lista resumida dos nomes de aplicativos disponíveis para alimentar a IA."""
        return list(self._index.keys())[:limit]

    def find_app(self, query: str) -> str | None:
        """Encontra o caminho do aplicativo ou jogo por correspondência intuitiva ou alias."""
        clean_q = normalize(query).strip()
        if not clean_q:
            return None
        aliased = POPULAR_ALIASES.get(clean_q, clean_q)

        for candidate in (aliased, clean_q):
            if candidate in self._index:
                return self._index[candidate]

        compact_q = aliased.replace(" ", "")
        for name, path in self._index.items():
            if compact_q == name.replace(" ", ""):
                return path

        for name, path in self._index.items():
            compact_name = name.replace(" ", "")
            if len(compact_q) >= 3 and (compact_q in compact_name or compact_name in compact_q):
                return path

        return None
