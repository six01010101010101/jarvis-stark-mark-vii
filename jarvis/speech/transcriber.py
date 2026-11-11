"""Motor de transcrição multicamada ultra-rápido (HTTPS L16 Direto + Google STT + Gemini)."""

from __future__ import annotations

import json
import logging
import re
import urllib.request
from urllib.parse import urlencode

import speech_recognition as sr

logger = logging.getLogger(__name__)

HTTPS_SPEECH_ENDPOINT = "https://www.google.com/speech-api/v2/recognize"
CHROMIUM_KEY = "AIzaSyBOti4mM-6x9WDnZIjIeyEU21OpBXqWBgw"
CHROME_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

LANGUAGE_PROFILES: dict[str, dict[str, str | None]] = {
    "auto": {"name": "🌐 Auto-Detectar (Poliglota)", "whisper_code": None, "bcp47": "pt-BR", "tts_voice": "pt-BR-AntonioNeural"},
    "pt":   {"name": "🇧🇷 Português (pt-BR)",       "whisper_code": "pt", "bcp47": "pt-BR", "tts_voice": "pt-BR-AntonioNeural"},
    "en":   {"name": "🇺🇸 English (en-US)",          "whisper_code": "en", "bcp47": "en-US", "tts_voice": "en-GB-RyanNeural"},
    "es":   {"name": "🇪🇸 Español (es-ES)",          "whisper_code": "es", "bcp47": "es-ES", "tts_voice": "es-ES-AlvaroNeural"},
    "ja":   {"name": "🇯🇵 日本語 (ja-JP)",            "whisper_code": "ja", "bcp47": "ja-JP", "tts_voice": "ja-JP-KeitaNeural"},
    "fr":   {"name": "🇫🇷 Français (fr-FR)",         "whisper_code": "fr", "bcp47": "fr-FR", "tts_voice": "fr-FR-HenriNeural"},
    "de":   {"name": "🇩🇪 Deutsch (de-DE)",          "whisper_code": "de", "bcp47": "de-DE", "tts_voice": "de-DE-ConradNeural"},
    "it":   {"name": "🇮🇹 Italiano (it-IT)",         "whisper_code": "it", "bcp47": "it-IT", "tts_voice": "it-IT-DiegoNeural"},
}


def unpack_transcription(raw_result: object) -> tuple[str, str]:
    """Desempacota de forma segura qualquer saída do transcriber (tuple, dict ou str) para (texto, idioma)."""
    if raw_result is None:
        return "", "pt"
    if isinstance(raw_result, tuple):
        text = str(raw_result[0] or "").strip() if len(raw_result) > 0 else ""
        lang = str(raw_result[1] or "pt").strip() if len(raw_result) > 1 else "pt"
        return text, lang
    if isinstance(raw_result, dict):
        return str(raw_result.get("text", "")).strip(), str(raw_result.get("lang", "pt")).strip()
    return str(raw_result).strip(), "pt"


def detect_language_code(text: str, default: str = "pt") -> str:
    if re.search(r"[\u3040-\u30ff\u4e00-\u9fff]", text):
        return "ja"
    words = set(re.findall(r"\b\w+\b", text.lower()))
    if words & {"the", "what", "how", "open", "close", "please", "weather", "time", "hello", "who"}:
        return "en"
    if words & {"hola", "como", "estas", "abrir", "cerrar", "tiempo", "gracias", "donde"} and "o" not in words:
        return "es"
    if words & {"bonjour", "merci", "ouvrir", "fermer", "comment", "quel", "avec"}:
        return "fr"
    if words & {"hallo", "danke", "bitte", "wie", "oeffnen", "schliessen", "uhr"}:
        return "de"
    return default


class MultiEngineTranscriber:
    """Converte áudio capturado em texto em tempo real com ou sem VPN."""

    def __init__(
        self,
        recognizer: sr.Recognizer,
        language: str = "pt-BR",
        gemini: object | None = None,
    ) -> None:
        self._recognizer = recognizer
        self._language = language
        self._gemini = gemini
        self.selected_lang_mode = "pt"
        self.last_detected_language = "pt"

    def set_language_mode(self, lang_code: str) -> None:
        code = lang_code.split("-")[0].lower() if "-" in lang_code else lang_code.lower()
        if code in LANGUAGE_PROFILES:
            self.selected_lang_mode = code
            if code != "auto":
                self._language = str(LANGUAGE_PROFILES[code]["bcp47"] or "pt-BR")
                self.last_detected_language = code
            print(f"[JARVIS IDIOMA] 🌐 Modo alterado para: {LANGUAGE_PROFILES[code]['name']}", flush=True)

    def transcribe(self, audio: sr.AudioData) -> tuple[str | None, str]:
        """Tenta transcrever o áudio através de múltiplas camadas de baixa latência."""
        # Camada 1: HTTPS Direto com PCM L16 16kHz e User-Agent Chrome (Mais rápido, sem flac.exe)
        text = self._transcribe_https_l16(audio)
        if text:
            self.last_detected_language = detect_language_code(text, self.selected_lang_mode if self.selected_lang_mode != "auto" else "pt")
            return text, "Google-HTTPS-Direct"

        # Camada 2: Recognizer Google via endpoint HTTPS explícito
        text = self._transcribe_google_https(audio)
        if text:
            self.last_detected_language = detect_language_code(text, self.selected_lang_mode if self.selected_lang_mode != "auto" else "pt")
            return text, "Google-STT"

        # Camada 3: Gemini Audio API Autenticada
        text = self._transcribe_gemini(audio)
        if text:
            self.last_detected_language = detect_language_code(text, self.selected_lang_mode if self.selected_lang_mode != "auto" else "pt")
            return text, "Gemini-Neural"

        return None, "None"

    def _transcribe_https_l16(self, audio: sr.AudioData) -> str | None:
        """Envia PCM 16-bit 16kHz diretamente via HTTPS com cabeçalho de navegador real."""
        try:
            raw_pcm = audio.get_raw_data(convert_rate=16000, convert_width=2)
            if not raw_pcm:
                return None
            params = urlencode({
                "client": "chromium",
                "lang": self._language,
                "key": CHROMIUM_KEY,
                "pFilter": 0,
            })
            url = f"{HTTPS_SPEECH_ENDPOINT}?{params}"
            req = urllib.request.Request(
                url,
                data=raw_pcm,
                headers={
                    "Content-Type": "audio/l16; rate=16000",
                    "User-Agent": CHROME_USER_AGENT,
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=2.8) as resp:
                body = resp.read().decode("utf-8", errors="ignore")
            return self._parse_chromium_json(body)
        except Exception as exc:
            logger.debug("Camada 1 (HTTPS L16) falhou: %s", exc)
            return None

    def _transcribe_google_https(self, audio: sr.AudioData) -> str | None:
        try:
            self._recognizer.operation_timeout = 2.8
            res = self._recognizer.recognize_google(
                audio,
                language=self._language,
                endpoint=HTTPS_SPEECH_ENDPOINT,
            )
            clean = str(res).strip()
            return clean if clean else None
        except Exception as exc:
            logger.debug("Camada 2 (Google STT HTTPS) falhou: %s", exc)
            return None

    def _transcribe_gemini(self, audio: sr.AudioData) -> str | None:
        if not self._gemini or not hasattr(self._gemini, "transcribe_audio"):
            return None
        try:
            wav_bytes = audio.get_wav_data(convert_rate=16000, convert_width=2)
            clean = self._gemini.transcribe_audio(wav_bytes)
            return str(clean).strip() if clean else None
        except Exception as exc:
            logger.debug("Camada 3 (Gemini Audio) falhou: %s", exc)
            return None

    @staticmethod
    def _parse_chromium_json(response_text: str) -> str | None:
        for line in response_text.splitlines():
            line_str = line.strip()
            if not line_str:
                continue
            try:
                data = json.loads(line_str)
                results = data.get("result", [])
                if results:
                    alts = results[0].get("alternative", [])
                    if alts and "transcript" in alts[0]:
                        transcript = str(alts[0]["transcript"]).strip()
                        if transcript:
                            return transcript
            except Exception:
                continue
        return None
