"""Serviço de IA Gemini com busca em fontes do Google e Cérebro Local Stark integrado."""

from __future__ import annotations

import json
import logging
from google import genai
from google.genai import types

from jarvis.services.local_brain import LocalStarkBrain

logger = logging.getLogger(__name__)

JARVIS_PERSONA = (
    "Você é o J.A.R.V.I.S., a inteligência artificial do Tony Stark atendendo o Ken. "
    "Responda em português do Brasil de forma natural, culta e direta, sem ficar repetindo 'sim senhor' toda hora. "
    "Use dados reais de história, ciência, clima e internet. "
    "Use no máximo 30 palavras, sem markdown, asteriscos ou emojis, pois será lido em voz alta."
)
TEMPERATURE = 0.7
REQUEST_TIMEOUT_MS = 4_500
MAX_ATTEMPTS = 1

MIND_SYSTEM_PROMPT = (
    "Você é a MENTE de J.A.R.V.I.S., assistente no Windows do Ken. "
    "Aplicativos e navegadores conhecidos: Google Chrome, Microsoft Edge, Bloco de Notas, Calculadora, "
    "Paint, VS Code, Discord, Spotify, Steam, WhatsApp, YouTube, Instagram, TikTok, Fortnite, Counter-Strike 2. "
    "Classifique a fala de Ken em JSON rigoroso (sem ficar repetindo 'sim senhor'):\n"
    '- Se pedir para abrir programa/navegador: {"action": "open_app", "target": "<executavel ou nome>", "reply": "Claro, abrindo <nome> agora."}\n'
    '- Se pedir para fechar programa/aba/janela: {"action": "close_app", "target": "<nome, aba ou janela>", "reply": "Certo, encerrando <nome>."}\n'
    '- Se pedir YouTube, Instagram, WhatsApp ou site: {"action": "open_url", "target": "<url completa>", "reply": "Colocando no <nome> agora."}\n'
    '- Se for pergunta de história, clima, horário ou conversa: {"action": "chat", "target": "", "reply": "<resposta direta e natural, max 30 palavras>"}\n'
    "Responda APENAS o JSON válido."
)


class GeminiAnswerService:
    """Mente cognitiva com Google Search Grounding e integração com Cérebro Local + Web."""

    def __init__(self, api_key: str, model: str, client: genai.Client | None = None) -> None:
        self._model = "gemini-2.0-flash" if ("3.5" in model or "2.5" in model) else model
        self._client = client or genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(
                timeout=REQUEST_TIMEOUT_MS,
                retry_options=types.HttpRetryOptions(attempts=MAX_ATTEMPTS),
            ),
        )
        self._chat = self._client.chats.create(
            model=self._model,
            config=types.GenerateContentConfig(
                system_instruction=JARVIS_PERSONA,
                temperature=TEMPERATURE,
                candidate_count=1,
            ),
        )

    def ask(self, question: str) -> str:
        """Responde perguntas usando Gemini com Google Search ou fontes da Web em tempo real."""
        try:
            res = self._client.models.generate_content(
                model=self._model,
                contents=question,
                config=types.GenerateContentConfig(
                    system_instruction=JARVIS_PERSONA,
                    temperature=TEMPERATURE,
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                ),
            )
            text = (res.text or "").strip()
            if text:
                return text
        except Exception:
            try:
                response = self._chat.send_message(question)
                text = (response.text or "").strip()
                if text:
                    return text
            except Exception as exc:
                logger.debug("Usando motor de conhecimento Web/Local em ask(): %s", exc)
        return LocalStarkBrain.resolve_intent(question)["reply"]

    def interpret_intent(self, utterance: str) -> dict[str, str]:
        """Decifra a intenção via motor local imediato + Gemini + fontes da Internet."""
        local_res = LocalStarkBrain.resolve_intent(utterance)
        if local_res.get("action") in ("open_app", "open_url", "close_app") or local_res.get("source") == "verified":
            return local_res

        prompt = f"{MIND_SYSTEM_PROMPT}\n\nKen disse:\n\"{utterance}\""
        try:
            res = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json"),
            )
            raw = (res.text or "").strip()
            data = json.loads(raw)
            return {
                "action": str(data.get("action", "chat")),
                "target": str(data.get("target", "")),
                "reply": str(data.get("reply", "")),
            }
        except Exception as exc:  # noqa: BLE001
            logger.debug("Mente Local/Web assumindo resposta (%s)", exc)
            return local_res

    def transcribe_audio(self, wav_bytes: bytes) -> str | None:
        """Transcreve áudio via API oficial autenticada do Gemini."""
        prompt = "Transcreva rigorosamente o que foi falado neste áudio em português. Retorne APENAS o texto falado, sem aspas e sem explicações."
        for m in ("gemini-2.0-flash", "gemini-1.5-flash"):
            try:
                res = self._client.models.generate_content(
                    model=m,
                    contents=[types.Part.from_bytes(data=wav_bytes, mime_type="audio/wav"), prompt],
                )
                text = (res.text or "").strip().strip('"').strip("'")
                if text:
                    return text
            except Exception as exc:  # noqa: BLE001
                logger.debug("Tentativa de transcrição com %s falhou: %s", m, exc)
                continue
        return None
