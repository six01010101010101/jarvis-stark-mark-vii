"""Serviço de IA Gemini Poliglota com Mente Coletiva, Autoconsciência Mark VII e Conversação."""

from __future__ import annotations

import json
import logging
from google import genai
from google.genai import types

from jarvis.services.collective_prompts import JARVIS_COLLECTIVE_MIND_PROMPT, MIND_CLASSIFICATION_PROMPT
from jarvis.services.conversational_engine import ConversationalEngine
from jarvis.services.local_brain import LocalStarkBrain

logger = logging.getLogger(__name__)

TEMPERATURE = 0.75
REQUEST_TIMEOUT_MS = 4_500
MAX_ATTEMPTS = 1


class GeminiAnswerService:
    """Mente Coletiva Poliglota com inteligência profunda, autoconsciência Stark Mark VII e diálogo humanizado."""

    def __init__(self, api_key: str, model: str, client: genai.Client | None = None) -> None:
        self._model = "gemini-2.0-flash" if ("3.5" in model or "2.5" in model) else model
        self._detected_language = "pt-BR"
        self._client = client or genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(
                timeout=REQUEST_TIMEOUT_MS,
                retry_options=types.HttpRetryOptions(attempts=MAX_ATTEMPTS),
            ),
        )
        self._conversational = ConversationalEngine(client=self._client, model=self._model)
        self._chat = self._client.chats.create(
            model=self._model,
            config=types.GenerateContentConfig(
                system_instruction=self._build_system_prompt(),
                temperature=TEMPERATURE,
                candidate_count=1,
            ),
        )

    def _build_system_prompt(self) -> str:
        return (
            f"{JARVIS_COLLECTIVE_MIND_PROMPT}\n\n"
            f"Responda SEMPRE no mesmo idioma em que o usuário falou ({self._detected_language}). "
            f"Ofereça respostas ricas, perspicazes e amigáveis, mantendo a postura de conselheiro e companheiro genial."
        )

    def set_language(self, idioma_detectado: str) -> None:
        """Define o idioma detectado para resposta Poliglota dinâmica."""
        self._detected_language = idioma_detectado or "pt-BR"

    def ask(self, question: str) -> str:
        """Responde via Mente Coletiva profunda do Gemini com Google Search ou Motor Conversacional."""
        sys_prompt = self._build_system_prompt()
        try:
            res = self._client.models.generate_content(
                model=self._model,
                contents=question,
                config=types.GenerateContentConfig(
                    system_instruction=sys_prompt,
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
                logger.debug("Mente Coletiva Local assumindo resposta em ask(): %s", exc)
        return self._conversational.generate_reply(question, lang=self._detected_language)

    def interpret_intent(self, utterance: str) -> dict[str, str]:
        """Decifra a intenção do usuário: comandos de sistema imediatos ou diálogo profundo."""
        local_res = LocalStarkBrain.resolve_intent(utterance)
        if local_res.get("action") in ("open_app", "open_url", "close_app", "close_tab", "close_window"):
            return local_res

        sys_mind = f"{JARVIS_COLLECTIVE_MIND_PROMPT}\n\n{MIND_CLASSIFICATION_PROMPT.format(idioma_detectado=self._detected_language)}"
        prompt = f"{sys_mind}\n\nKen disse:\n\"{utterance}\""
        try:
            res = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json", temperature=TEMPERATURE),
            )
            raw = (res.text or "").strip()
            data = json.loads(raw)
            reply = str(data.get("reply", "")).strip()
            if reply:
                return {
                    "action": str(data.get("action", "chat")),
                    "target": str(data.get("target", "")),
                    "reply": reply,
                }
        except Exception as exc:
            logger.debug("Mente Conversacional assumindo resposta (%s)", exc)
        return local_res

    def transcribe_audio(self, wav_bytes: bytes) -> str | None:
        """Transcreve áudio Poliglota via API oficial autenticada do Gemini."""
        prompt = (
            "Transcreva rigorosamente apenas a fala humana presente neste áudio no idioma original falado. "
            "Se houver apenas ruído, latido, miado ou silêncio, retorne vazio. Sem aspas e sem explicações."
        )
        for m in ("gemini-2.0-flash", "gemini-1.5-flash"):
            try:
                res = self._client.models.generate_content(
                    model=m,
                    contents=[types.Part.from_bytes(data=wav_bytes, mime_type="audio/wav"), prompt],
                )
                text = (res.text or "").strip().strip('"').strip("'")
                if text:
                    return text
            except Exception as exc:
                logger.debug("Tentativa de transcrição com %s falhou: %s", m, exc)
                continue
        return None
