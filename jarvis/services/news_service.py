"""Serviço de notícias em tempo real via feeds informativos abertos."""

from __future__ import annotations

import logging
import re
import urllib.request
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

RSS_URL = "https://news.google.com/rss?hl=pt-BR&gl=BR&ceid=BR:pt-419"
TIMEOUT_SECONDS = 4.0


class NewsService:
    """Busca e resume as principais notícias do Brasil e do mundo em tempo real."""

    def get_headlines(self, limit: int = 3) -> str:
        """Obtém as notícias mais relevantes do momento."""
        try:
            req = urllib.request.Request(RSS_URL, headers={"User-Agent": "JarvisAssistant/1.0"})
            with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
                xml_data = resp.read()

            root = ET.fromstring(xml_data)
            items = root.findall(".//item")
            if not items:
                return "Não consegui obter o resumo de notícias no momento, senhor."

            headlines: list[str] = []
            for item in items[:limit]:
                title_elem = item.find("title")
                if title_elem is not None and title_elem.text:
                    clean = re.sub(r"\s+-\s+[^-]+$", "", title_elem.text).strip()
                    headlines.append(clean)

            if not headlines:
                return "Nenhuma manchete disponível no momento, senhor."

            formatted = [f"Notícia {i+1}: {title}" for i, title in enumerate(headlines)]
            return "Aqui estão as principais notícias do momento, senhor Ken: " + ". ".join(formatted) + "."
        except Exception as exc:  # noqa: BLE001
            logger.warning("Falha ao consultar feed de notícias: %s", exc)
            return "Não foi possível conectar aos canais de notícias no momento, senhor."
