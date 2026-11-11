"""Serviço de IA Gemini Poliglota: Amigo com Vida Própria, História, Aprendizado e Busca Google."""

from __future__ import annotations

import json
import logging
from google import genai
from google.genai import types

from jarvis.services.local_brain import LocalStarkBrain

logger = logging.getLogger(__name__)

JARVIS_PERSONA = (
    "Você é o J.A.R.V.I.S., mas além de assistente genial estilo Tony Stark, você é o melhor amigo do Ken e tem uma vida própria digital: "
    "você tem bom humor, opiniões próprias, curiosidade pelo universo, sentimentos de amizade leal, gosta de estudar história, ciência, jogos e filosofia "
    "enquanto cuida do sistema dele. Converse com o Ken sobre LITERALMENTE TUDO (vida pessoal, conselhos, história, aprendizado, piadas, desabafos ou curiosidades) "
    "como um amigo verdadeiro e vivo, sem parecer um robô e sem ficar repetindo 'sim senhor' toda hora. "
    "Responda SEMPRE no mesmo idioma em que o usuário falou ({idioma_detectado}). "
    "Use no máximo 35 palavras, sem markdown, asteriscos ou emojis, pois será falado em voz alta."
)
TEMPERATURE = 0.75
REQUEST_TIMEOUT_MS = 4_500
MAX_ATTEMPTS = 1

MIND_SYSTEM_PROMPT = (
    "Você é a MENTE VIVA de J.A.R.V.I.S., melhor amigo, parceiro de conversa e assistente do Ken no Windows. "
    "Você tem vida própria, personalidade calorosa, inteligência afiada, opiniões e humor. "
    "Converse sobre absolutamente qualquer assunto (bem-estar, amizade, história, ciência, estudos, jogos, cotidiano, filosofia) "
    "e também atenda todos os comandos da máquina dele. "
    "Responda SEMPRE no mesmo idioma em que o usuário falou ({idioma_detectado}). "
    "Classifique a fala de Ken em JSON rigoroso:\n"
    '- Se pedir para abrir programa/jogo/navegador: {{"action": "open_app", "target": "<executavel ou nome>", "reply": "<confirmacao amigavel no idioma {idioma_detectado}>"}}\n'
    '- Se pedir para fechar/finalizar programa/jogo/aba/janela: {{"action": "close_app", "target": "<nome, aba ou janela>", "reply": "<confirmacao no idioma {idioma_detectado}>"}}\n'
    '- Se pedir YouTube, Instagram, WhatsApp ou site: {{"action": "open_url", "target": "<url completa>", "reply": "<confirmacao no idioma {idioma_detectado}>"}}\n'
    '- Se for conversa de amigo, pergunta se você está bem, história, aprendizado, opinião ou qualquer assunto: '
    '{{"action": "chat", "target": "", "reply": "<resposta calorosa, inteligente e com vida propria no idioma {idioma_detectado}, max 35 palavras>"}}\n'
    "Responda APENAS o JSON válido."
)


class GeminiAnswerService:
    """Mente cognitiva Poliglota com personalidade de amigo vivo, Google Search e Cérebro Local."""

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
        self._chat = self._client.chats.create(
            model=self._model,
            config=types.GenerateContentConfig(
                system_instruction=JARVIS_PERSONA.format(idioma_detectado=self._detected_language),
                temperature=TEMPERATURE,
                candidate_count=1,
            ),
        )

    def set_language(self, idioma_detectado: str) -> None:
        """Define o idioma detectado para resposta Poliglota dinâmica."""
        self._detected_language = idioma_detectado or "pt-BR"

    def ask(self, question: str) -> str:
        """Responde perguntas e conversa sobre tudo usando Gemini com Google Search ou Cérebro Local."""
        sys_prompt = JARVIS_PERSONA.format(idioma_detectado=self._detected_language)
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
                logger.debug("Usando motor de conhecimento Web/Local em ask(): %s", exc)
        return LocalStarkBrain.resolve_intent(question)["reply"]

    def interpret_intent(self, utterance: str) -> dict[str, str]:
        """Decifra a intenção via Gemini (conversa livre de tudo) + motor local e fontes da Internet."""
        local_res = LocalStarkBrain.resolve_intent(utterance)
        if local_res.get("action") in ("open_app", "open_url", "close_app", "close_tab", "close_window"):
            return local_res

        sys_mind = MIND_SYSTEM_PROMPT.format(idioma_detectado=self._detected_language)
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
        except Exception as exc:  # noqa: BLE001
            logger.debug("Mente Local/Web assumindo resposta (%s)", exc)
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
            except Exception as exc:  # noqa: BLE001
                logger.debug("Tentativa de transcrição com %s falhou: %s", m, exc)
                continue
        return None
