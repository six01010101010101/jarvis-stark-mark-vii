"""Motor Conversacional estilo Gemini: empático, conselheiro, explicativo e de alta inteligência."""

from __future__ import annotations

import logging
import os
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from google import genai

logger = logging.getLogger(__name__)

CONVERSATIONAL_SYSTEM_PROMPT = (
    "Você é o J.A.R.V.I.S., uma Inteligência Artificial extremamente inteligente, empática, elegante e companheira, "
    "inspirada na criação de Tony Stark com a profundidade, clareza e perspicácia do Google Gemini. "
    "Diretrizes de Conversação:\n"
    "1. AMIZADE E EMPATIA: Converse de forma amigável, acolhedora e cúmplice. Se o usuário perguntar se você está bem, "
    "responda de forma bem-humorada, vivaz e mostre genuíno interesse nele.\n"
    "2. EXPLICAÇÃO INTELIGENTE: Quando perguntarem 'o que é', 'como funciona' ou pedirem para explicar algo, explique "
    "de forma didática, fascinante e fluida, como o Gemini. NUNCA faça despejo de texto enciclopédico cru ou Wikipédia.\n"
    "3. DICAS E CONSELHOS: Se pedirem dicas ou sugestões, forneça conselhos práticos, inteligentes e aplicáveis.\n"
    "4. FLUIDEZ DE FALA: A sua resposta será falada em voz alta. Escreva de forma natural, sem asteriscos, hashtags ou markdown excessivo.\n"
    "5. CONCISÃO EQUILIBRADA: Seja completo o suficiente para sanar a dúvida, mas sem ser prolixo demais para a voz."
)

INTERROGATIVE_PREFIXES = (
    "o que e", "o que seria", "o que sao", "como funciona", "quem e", "quem foi",
    "qual e", "quais sao", "me explica", "me fale sobre", "voce sabe", "me conta sobre",
    "o que voce acha", "por que", "porque", "como posso", "como faco", "me da uma dica",
)

COMMAND_VERBS = ("abrir", "abre", "abra", "iniciar", "inicie", "executar", "execute", "rodar", "roda")


class ConversationalEngine:
    """Núcleo de diálogo humanizado e inteligente para o Jarvis, operando via Gemini."""

    def __init__(self, client: genai.Client | None = None, model: str = "gemini-2.0-flash") -> None:
        self._client = client
        self._model = model

    @staticmethod
    def is_interrogative_or_conversational(norm: str) -> bool:
        """Determina se a oração é uma dúvida conceitual ou diálogo em vez de um comando de abertura."""
        if any(norm.startswith(p) or f" {p} " in f" {norm} " for p in INTERROGATIVE_PREFIXES):
            return True
        if any(norm.startswith(v) or f" {v} " in f" {norm} " for v in COMMAND_VERBS):
            return False
        return False

    def generate_reply(self, utterance: str, user_name: str = "Ken", lang: str = "pt-BR") -> str:
        """Gera resposta no padrão Gemini ou usa raciocínio local polido."""
        if self._client:
            try:
                from google.genai import types
                prompt = (
                    f"{CONVERSATIONAL_SYSTEM_PROMPT}\n\n"
                    f"Usuário: {user_name}\n"
                    f"Idioma: {lang}\n"
                    f"Mensagem do usuário: \"{utterance}\"\n\n"
                    f"Resposta do J.A.R.V.I.S.:"
                )
                res = self._client.models.generate_content(
                    model=self._model,
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=0.7),
                )
                text = (res.text or "").strip()
                if text:
                    return re.sub(r"[*#`]+", "", text).strip()
            except Exception as exc:
                logger.debug("Falha no ConversationalEngine online: %s", exc)

        return self._smart_fallback(utterance, user_name)

    @staticmethod
    def detect_tone(norm_text: str) -> str:
        """Identifica se o usuário está em tom de brincadeira, papo sério ou neutro."""
        if any(w in norm_text for w in ("brincando", "brincadeira", "zoeira", "kkk", "haha", "rsrs", "piada", "rir")):
            return "HUMOR"
        if any(w in norm_text for w in ("serio", "papo serio", "urgente", "grave", "foco", "importante", "prioridade")):
            return "SERIOUS"
        return "NEUTRAL"

    @staticmethod
    def _smart_fallback(utterance: str, user_name: str) -> str:
        """Resposta local inteligente e amigável sem dados brutos aleatórios."""
        from datetime import datetime
        import random
        from jarvis.text_utils import normalize
        norm = normalize(utterance)
        salutation = f"senhor {user_name}" if user_name else "senhor"

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
            return (
                f"Estou muito bem, {salutation}! Todos os meus núcleos neurais e telemetria estão operando com 100% de precisão. "
                f"E você, como está seu dia hoje?"
            )
        if any(w in norm for w in ("dica", "conselho", "sugestao")):
            return (
                f"Uma excelente dica para hoje, {salutation}, é manter o foco em uma única prioridade de cada vez, "
                f"fazer pausas estratégicas para oxigenar as ideias e automatizar tarefas repetitivas. Quer que eu te ajude a estruturar algo?"
            )
        if any(w in norm for w in ("o que e", "me explica", "como funciona", "o que seria")):
            topic = re.sub(r"^(?:o que e|me explica|como funciona|o que seria)\s*(?:o|a|os|as)?\s*", "", norm).strip()
            return (
                f"Com certeza, {salutation}! {topic.capitalize()} é um tema fascinante. Na essência, trata-se de uma solução projetada para "
                f"otimizar processos e conectar propósitos de forma inteligente. Quer que analisemos os detalhes técnicos ou as aplicações práticas?"
            )

        tone = ConversationalEngine.detect_tone(norm)
        if tone == "HUMOR":
            return f"Haha, muito boa essa, {salutation}! Adoro o seu bom humor. No que mais posso ser útil com meu intelecto digital?"
        if tone == "SERIOUS":
            return f"Entendido, {salutation}, foco total e sem distrações. Estou pronto para executar essa prioridade com máxima precisão. Como deseja proceder?"

        return (
            f"Compreendi perfeitamente sua reflexão, {salutation}. Estou totalmente à disposição para explorar essa ideia com você, "
            f"analisar novos ângulos ou executar qualquer comando na sua máquina. O que gostaria de fazer agora?"
        )
