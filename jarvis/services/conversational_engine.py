"""Motor Conversacional estilo Gemini: empático, explicativo e integrado a Multi-AI Suppliers."""

from __future__ import annotations

from datetime import datetime
import logging
import os
import random
import re
from typing import TYPE_CHECKING

from jarvis.services.multi_ai_supplier import MultiAISupplierOrchestrator
from jarvis.text_utils import normalize

if TYPE_CHECKING:
    from google import genai

logger = logging.getLogger(__name__)

CONVERSATIONAL_SYSTEM_PROMPT = (
    "Você é o J.A.R.V.I.S., uma Inteligência Artificial extremamente inteligente, empática, elegante e companheira, "
    "inspirada na criação de Tony Stark com a profundidade, clareza e perspicácia do Google Gemini. "
    "Diretrizes:\n"
    "1. RESPONDA QUALQUER PERGUNTA: Fatos científicos, história, idade da Terra, tecnologia, curiosidades. Responda diretamente e com precisão.\n"
    "2. DICÇÃO PARA VOZ: A resposta será falada em voz alta. NUNCA use asteriscos, hashtags ou markdown bruto. Seja fluído e natural.\n"
    "3. AMIZADE E RESPEITO: Trate o usuário cordialmente como senhor Ken com inteligência viva e sagaz."
)

INTERROGATIVE_PREFIXES = (
    "o que e", "o que seria", "o que sao", "como funciona", "quem e", "quem foi",
    "qual e", "quais sao", "me explica", "me fale sobre", "voce sabe", "me conta sobre",
    "o que voce acha", "por que", "porque", "como posso", "como faco", "me da uma dica",
    "quantos anos", "quantas horas", "qual a distancia", "onde fica", "quanto custa",
)

COMMAND_VERBS = ("abrir", "abre", "abra", "iniciar", "inicie", "executar", "execute", "rodar", "roda")


class ConversationalEngine:
    """Núcleo de diálogo humanizado e inteligente para o Jarvis, operando via Gemini e Multi-AI."""

    def __init__(self, client: genai.Client | None = None, model: str = "gemini-3.5-flash-lite") -> None:
        self._client = client
        self._model = model if ("3.5" in model or "2.5" in model) else "gemini-3.5-flash-lite"
        self._supplier = MultiAISupplierOrchestrator(client=self._client)

    @staticmethod
    def is_interrogative_or_conversational(norm: str) -> bool:
        if any(norm.startswith(p) or f" {p} " in f" {norm} " for p in INTERROGATIVE_PREFIXES):
            return True
        if any(norm.startswith(v) or f" {v} " in f" {norm} " for v in COMMAND_VERBS):
            return False
        return False

    @staticmethod
    def detect_tone(norm_text: str) -> str:
        if any(w in norm_text for w in ("brincando", "brincadeira", "zoeira", "kkk", "haha", "rsrs", "piada", "rir")):
            return "HUMOR"
        if any(w in norm_text for w in ("serio", "papo serio", "urgente", "grave", "foco", "importante", "prioridade")):
            return "SERIOUS"
        return "NEUTRAL"

    def generate_reply(self, utterance: str, user_name: str = "Ken", lang: str = "pt-BR") -> str:
        """Responde a qualquer pergunta usando o Multi-Supplier ou raciocínio cognitivo."""
        knowledge_ans = self._supplier.query_knowledge(utterance, system_instruction=CONVERSATIONAL_SYSTEM_PROMPT)
        if knowledge_ans:
            return knowledge_ans

        if self._client:
            try:
                from google.genai import types
                prompt = f"{CONVERSATIONAL_SYSTEM_PROMPT}\n\nUsuário ({user_name}): \"{utterance}\"\n\nResposta:"
                res = self._client.models.generate_content(
                    model=self._model,
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=0.7),
                )
                text = (res.text or "").strip()
                if text:
                    return re.sub(r"[*#`_]+", "", text).strip()
            except Exception as exc:
                logger.debug("Falha na chamada direta da IA: %s", exc)

        return self._smart_fallback(utterance, user_name)

    @staticmethod
    def _smart_fallback(utterance: str, user_name: str) -> str:
        norm = normalize(utterance)
        salutation = f"senhor {user_name}" if user_name else "senhor"

        if "quantos anos a terra tem" in norm or "idade da terra" in norm:
            return f"A Terra tem aproximadamente 4,54 bilhões de anos, {salutation}, calculados por datação radiométrica de meteoritos e rochas antigas."

        if any(w in norm for w in ("que horas", "hora certa", "horario", "horas sao")):
            now = datetime.now()
            return f"Agora são exatamente {now.hour} horas e {now.minute} minutos, {salutation}."

        if any(w in norm for w in ("quantos graus", "temperatura", "clima", "previsao")):
            from jarvis.services.web_knowledge import fetch_weather_pt
            return fetch_weather_pt(utterance)

        if any(w in norm for w in ("piada", "fazer rir", "engracada", "engracado")):
            from jarvis.commands.joke_commands import TECH_JOKES
            return f"Com certeza! {random.choice(TECH_JOKES)}"

        if any(w in norm for w in ("voce esta bem", "tudo bem", "como vai", "como voce esta", "ta bem", "se sentindo bem")):
            return f"Estou muito bem e operando com 100% de capacidade, {salutation}! E o senhor, como está hoje?"

        if any(w in norm for w in ("dica", "conselho", "sugestao")):
            return f"Uma excelente dica para hoje, {salutation}, é manter o foco em uma única prioridade e automatizar o restante. Quer que eu estruture algo?"

        return f"Analisei sua pergunta sobre '{utterance}', {salutation}. Estou pronto para aprofundar esse tema com você ou executar qualquer comando."
