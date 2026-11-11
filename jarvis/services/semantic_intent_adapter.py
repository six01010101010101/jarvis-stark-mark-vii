"""Adaptador de intenção semântica para falas abreviadas, gírias e sotaques."""

from __future__ import annotations

import re
from typing import Any

from jarvis.text_utils import normalize

YT_PREFIXES = (
    r"^(?:poe\s+no\s+yt|põe\s+no\s+yt|bota\s+no\s+yt|toca\s+no\s+yt|joga\s+no\s+yt)\s+(.+)",
    r"^(?:bota\s+uma\s+musica\s+de|bota\s+um\s+som\s+de|toca\s+um\s+som\s+do|toca\s+um\s+som\s+da)\s+(.+)",
    r"^(?:solta\s+o\s+som|manda\s+tocar|coloca\s+pra\s+tocar|solta\s+a\s+musica\s+de)\s+(.+)",
    r"^(?:busca\s+no\s+youtube|pesquisa\s+no\s+youtube|tocar\s+no\s+youtube)\s+(.+)",
)

EXPLORER_SELECT_PREFIXES = (
    r"^(?:destaca\s+o\s+arquivo|seleciona\s+o\s+arquivo|mostra\s+o\s+arquivo|acha\s+o\s+arquivo)\s+(.+)",
    r"^(?:localiza\s+o\s+arquivo|onde\s+esta\s+o\s+arquivo|encontra\s+o\s+arquivo)\s+(.+)",
)

EXPLORER_OPEN_PREFIXES = (
    r"^(?:abre\s+a\s+pasta|vai\s+na\s+pasta|acessa\s+a\s+pasta|abre\s+o\s+explorer\s+em)\s+(.+)",
    r"^(?:vai\s+nos\s+downloads|vai\s+na\s+area\s+de\s+trabalho|vai\s+nos\s+documentos)\s*",
)


class SemanticIntentAdapter:
    """Interpreta variações coloquiais, abreviações e gírias do usuário."""

    @classmethod
    def parse_colloquial_action(cls, utterance: str) -> dict[str, Any] | None:
        """Mapeia orações informais ou regionais para ações executáveis do sistema."""
        norm = normalize(utterance)

        # 1. YouTube e músicas coloquiais
        for pat in YT_PREFIXES:
            m = re.search(pat, norm)
            if m:
                target = m.group(1).strip()
                target = re.sub(r"^(?:do|da|de)\s+", "", target).strip()
                return {"action": "play_youtube", "target": target}

        # 2. Seleção de arquivos no Explorer
        for pat in EXPLORER_SELECT_PREFIXES:
            m = re.search(pat, norm)
            if m:
                target = m.group(1).strip()
                return {"action": "select_file", "target": target}

        # 3. Abertura de pastas no Explorer
        for pat in EXPLORER_OPEN_PREFIXES:
            m = re.search(pat, norm)
            if m:
                folder = m.group(1).strip() if m.groups() else ""
                return {"action": "open_folder", "target": folder or norm}

        # 4. Pausar ou despausar vídeo / mídia
        if any(p in norm for p in ("pausa ai", "pausa o video", "pausa a musica", "pausar video", "pausar musica", "despausa ai", "volta a tocar", "continua o video")):
            return {"action": "toggle_media_pause", "target": ""}

        # 5. Retomada de fala interrompida
        if any(p in norm for p in ("retome a conversa", "retoma a conversa", "continue a falar", "continue jarvis", "volte a falar", "prossegue jarvis", "continue falando")):
            return {"action": "resume_speech", "target": ""}

        return None
