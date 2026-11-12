"""Orquestrador de Múltiplos Provedores de IA (Gemini, Google Search AI e modelos vigentes)."""

from __future__ import annotations

import logging
import os
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from google import genai

logger = logging.getLogger(__name__)

ACTIVE_GEMINI_MODELS: tuple[str, ...] = (
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.5-pro",
)


class MultiAISupplierOrchestrator:
    """Orquestrador resiliente inspirado no g-ai-desktop para consulta a múltiplos modelos de IA."""

    def __init__(self, client: genai.Client | None = None, api_key: str | None = None) -> None:
        self._client = client
        self._api_key = api_key or os.getenv("GEMINI_API_KEY", "")

    def _get_client(self) -> genai.Client | None:
        if self._client:
            return self._client
        if not self._api_key:
            return None
        try:
            from google import genai
            self._client = genai.Client(api_key=self._api_key)
            return self._client
        except Exception as exc:
            logger.debug("Falha ao instanciar genai.Client no orchestrator: %s", exc)
            return None

    def query_knowledge(self, question: str, system_instruction: str = "") -> str | None:
        """Consulta modelos ativos em cascata até obter resposta factual de alta inteligência."""
        client = self._get_client()
        if not client:
            return None

        from google.genai import types

        config = types.GenerateContentConfig(
            temperature=0.7,
            candidate_count=1,
            tools=[types.Tool(google_search=types.GoogleSearch())],
        )
        if system_instruction:
            config.system_instruction = system_instruction

        for model_name in ACTIVE_GEMINI_MODELS:
            try:
                res = client.models.generate_content(
                    model=model_name,
                    contents=question,
                    config=config,
                )
                text = (res.text or "").strip()
                if text:
                    return self._clean_phonetic_text(text)
            except Exception as exc:
                logger.debug("Modelo %s falhou na consulta de conhecimento: %s", model_name, exc)
                continue

        return None

    @staticmethod
    def _clean_phonetic_text(raw_text: str) -> str:
        """Formata o texto da IA para dicção fonética natural no sintetizador de voz."""
        cleaned = re.sub(r"[*#`_~>]+", "", raw_text)
        cleaned = re.sub(r"\n{2,}", " ", cleaned)
        cleaned = re.sub(r"\s{2,}", " ", cleaned)
        return cleaned.strip()

    @staticmethod
    def list_suppliers() -> list[str]:
        return ["Google Gemini 3.5 Flash Lite", "Google Search AI Mode", "Google Gemini 3.5 Flash", "Google Gemini 2.5 Pro"]
