"""Motor de busca web e pesquisa de fatos em tempo real inspirado no OpenJarvis."""

from __future__ import annotations

import json
import logging
import re
import urllib.parse
import urllib.request
from typing import Any

logger = logging.getLogger(__name__)


class WebSearchEngine:
    """Busca em fontes abertas da Web para prover contexto em tempo real ao J.A.R.V.I.S."""

    def __init__(self, timeout: float = 4.0) -> None:
        self._timeout = timeout

    def search(self, query: str, max_results: int = 4) -> list[dict[str, str]]:
        """Executa busca na web retornando títulos, resumos e links."""
        clean_q = query.strip()
        if not clean_q or len(clean_q) < 3:
            return []

        results = self._search_wikipedia(clean_q, limit=max_results)
        if not results:
            results = self._search_duckduckgo_lite(clean_q, limit=max_results)
        return results[:max_results]

    def _search_wikipedia(self, query: str, limit: int = 4) -> list[dict[str, str]]:
        """Pesquisa artigos enciclopédicos e fatos na Wikipedia."""
        encoded = urllib.parse.quote_plus(query)
        url = f"https://pt.wikipedia.org/w/api.php?action=query&list=search&srsearch={encoded}&format=json"
        req = urllib.request.Request(url, headers={"User-Agent": "JarvisMarkVII/1.0 (Stark OS)"})
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="ignore"))
            items = data.get("query", {}).get("search", [])
            output: list[dict[str, str]] = []
            for item in items[:limit]:
                title = str(item.get("title", ""))
                raw_snippet = str(item.get("snippet", ""))
                clean_snippet = re.sub(r"<[^>]+>", "", raw_snippet).strip()
                page_url = f"https://pt.wikipedia.org/wiki/{urllib.parse.quote(title)}"
                output.append({
                    "title": title,
                    "snippet": clean_snippet,
                    "url": page_url,
                })
            return output
        except Exception as exc:
            logger.debug("Falha na consulta Wikipedia: %s", exc)
            return []

    def _search_duckduckgo_lite(self, query: str, limit: int = 4) -> list[dict[str, str]]:
        """Busca de contingência via DuckDuckGo Lite."""
        encoded = urllib.parse.quote_plus(query)
        url = f"https://lite.duckduckgo.com/lite/?q={encoded}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
            # Extrai snippets da tabela simples do DuckDuckGo Lite
            snippets = re.findall(r'<td class="result-snippet"[^>]*>(.*?)</td>', html, flags=re.DOTALL)
            links = re.findall(r'<a class="result-link"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html, flags=re.DOTALL)
            results: list[dict[str, str]] = []
            for i, snip in enumerate(snippets[:limit]):
                title = re.sub(r"<[^>]+>", "", links[i][1]).strip() if i < len(links) else f"Resultado {i+1}"
                url_found = links[i][0] if i < len(links) else ""
                clean_snip = re.sub(r"<[^>]+>", "", snip).strip()
                results.append({"title": title, "snippet": clean_snip, "url": url_found})
            return results
        except Exception as exc:
            logger.debug("Falha no DuckDuckGo Lite: %s", exc)
            return []

    def format_search_for_prompt(self, query: str) -> str:
        """Formata os resultados da busca em formato de briefing direto para a IA."""
        results = self.search(query)
        if not results:
            return ""
        lines: list[str] = [f"[PESQUISA EM TEMPO REAL NA WEB PARA: '{query}']"]
        for r in results:
            lines.append(f"- Fonte: {r['title']} ({r['url']})\n  Resumo: {r['snippet']}")
        return "\n".join(lines)
