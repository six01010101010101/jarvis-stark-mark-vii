"""Indexador de aplicativos e jogos instalados no computador em tempo real."""

from __future__ import annotations

import logging
from pathlib import Path

from jarvis.text_utils import normalize

logger = logging.getLogger(__name__)

SEARCH_DIRECTORIES = (
    Path.home() / "OneDrive" / "Área de Trabalho",
    Path.home() / "Desktop",
    Path(r"C:\Users\Public\Desktop"),
    Path(r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs"),
    Path.home() / r"AppData\Roaming\Microsoft\Windows\Start Menu\Programs",
)

POPULAR_ALIASES: dict[str, str] = {
    "fort": "fortnite",
    "fortn": "fortnite",
    "fortnite": "fortnite",
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
    """Escaneia e mapeia todos os jogos, executáveis e atalhos da máquina do usuário."""

    def __init__(self) -> None:
        self._index: dict[str, str] = {}
        self.refresh()

    def refresh(self) -> None:
        """Atualiza o mapa de atalhos e executáveis instalados no Windows."""
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

        self._index = new_index
        logger.info("Indexador de apps carregado: %d itens indexados.", len(self._index))

    def get_known_app_names(self, limit: int = 50) -> list[str]:
        """Retorna uma lista resumida dos nomes de aplicativos disponíveis para alimentar a IA."""
        return list(self._index.keys())[:limit]

    def find_app(self, query: str) -> str | None:
        """Encontra o caminho do aplicativo ou jogo por correspondência intuitiva ou alias."""
        clean_q = normalize(query).strip()
        aliased = POPULAR_ALIASES.get(clean_q, clean_q)

        # 1. Correspondência exata no índice
        if aliased in self._index:
            return self._index[aliased]

        # 2. Correspondência sem espaços
        compact_q = aliased.replace(" ", "")
        for name, path in self._index.items():
            compact_name = name.replace(" ", "")
            if compact_q == compact_name:
                return path

        # 3. Substring ou contém
        for name, path in self._index.items():
            compact_name = name.replace(" ", "")
            if compact_q in compact_name or compact_name in compact_q:
                return path

        return None
