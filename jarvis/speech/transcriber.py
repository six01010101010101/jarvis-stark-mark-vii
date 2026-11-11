"""Motor de transcrição Poliglota + Anti-Alucinação (GPU CUDA Whisper + HTTPS L16 + Gemini)."""

from __future__ import annotations

import io
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

NOISE_HALLUCINATIONS: set[str] = {
    "legendas por", "obrigado por assistir", "legendas pela comunidade", "inscreva-se",
    "thank you for watching", "subtitles by", "[música]", "[musica]", "música", "musica",
    "you", "uh", "um", "ah", "hm", "hmm", "latido", "miado",
}


def is_valid_human_transcription(text: str) -> bool:
    """Descarta transcrições com < 2 caracteres alfabéticos ou alucinações de ruído."""
    if not text:
        return False
    clean_lower = text.strip().lower()
    if any(h == clean_lower or (len(h) > 5 and h in clean_lower) for h in NOISE_HALLUCINATIONS):
        return False
    return len(re.findall(r"[^\W\d_]", clean_lower, flags=re.UNICODE)) >= 2


def detect_language_code(text: str, default: str = "pt") -> str:
    """Identifica o código do idioma a partir do texto transcrito quando em modo Auto-Detectar."""
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


class MultilingualSpeechProcessor:
    """Processador Poliglota com filtro anti-alucinação e seleção automática de voz do Jarvis."""

    def __init__(self, whisper_model: object | None = None) -> None:
        self.model = whisper_model
        self.selected_lang_mode = "pt"

    def set_language_mode(self, lang_code: str) -> None:
        code = lang_code.split("-")[0].lower() if "-" in lang_code else lang_code.lower()
        if code in LANGUAGE_PROFILES:
            self.selected_lang_mode = code
            print(f"[JARVIS IDIOMA] 🌐 Modo alterado para: {LANGUAGE_PROFILES[code]['name']}", flush=True)

    def transcribe_human_words_only(self, audio_data: object) -> tuple[str | None, str]:
        if self.model is None:
            return None, self.selected_lang_mode if self.selected_lang_mode != "auto" else "pt"
        forced_lang = LANGUAGE_PROFILES[self.selected_lang_mode]["whisper_code"]
        segments, info = self.model.transcribe(  # type: ignore[attr-defined]
            audio_data,
            language=forced_lang,
            beam_size=5,
            vad_filter=True,
            vad_parameters={"threshold": 0.75, "min_speech_duration_ms": 300, "min_silence_duration_ms": 1500},
            no_speech_threshold=0.6,
            log_prob_threshold=-1.0,
            condition_on_previous_text=False,
        )
        detected_lang = str(getattr(info, "language", "pt") if forced_lang is None else forced_lang)
        if forced_lang is None and float(getattr(info, "language_probability", 1.0)) < 0.65:
            return None, detected_lang
        full_text = " ".join(seg.text.strip() for seg in segments).strip()
        return (full_text, detected_lang) if is_valid_human_transcription(full_text) else (None, detected_lang)

    @staticmethod
    def get_voice_for_language(lang_code: str) -> str:
        code = lang_code.split("-")[0].lower() if "-" in lang_code else lang_code.lower()
        return str(LANGUAGE_PROFILES.get(code, LANGUAGE_PROFILES["en"])["tts_voice"] or "pt-BR-AntonioNeural")


class MultiEngineTranscriber:
    """Converte áudio humano validado em texto com suporte Poliglota e GPU CUDA."""

    def __init__(
        self, recognizer: sr.Recognizer, language: str = "pt-BR", gemini: object | None = None,
        device: str = "cuda", compute_type: str = "float16",
    ) -> None:
        self._recognizer, self._language, self._gemini = recognizer, language, gemini
        self.device, self.compute_type = device, compute_type
        self.last_detected_language = "pt"
        self._gpu_model: object | None = None
        self._init_gpu_accelerator()
        self.multilingual = MultilingualSpeechProcessor(self._gpu_model)

    def _init_gpu_accelerator(self) -> None:
        try:
            from faster_whisper import WhisperModel  # type: ignore[import-not-found]
            self._gpu_model = WhisperModel("small", device=self.device, compute_type=self.compute_type)
        except Exception:
            self._gpu_model = None

    def set_language_mode(self, lang_code: str) -> None:
        self.multilingual.set_language_mode(lang_code)
        mode = self.multilingual.selected_lang_mode
        if mode != "auto" and mode in LANGUAGE_PROFILES:
            self._language = str(LANGUAGE_PROFILES[mode]["bcp47"] or "pt-BR")
            self.last_detected_language = mode

    def transcribe(self, audio: sr.AudioData) -> tuple[str | None, str]:
        mode = self.multilingual.selected_lang_mode
        if self._gpu_model is not None:
            try:
                wav_io = io.BytesIO(audio.get_wav_data(convert_rate=16000, convert_width=2))
                text, det_lang = self.multilingual.transcribe_human_words_only(wav_io)
                if text:
                    self.last_detected_language = det_lang
                    return text, f"GPU-CUDA-Whisper ({det_lang})"
            except Exception:
                pass

        if mode == "auto" and self._gemini and hasattr(self._gemini, "transcribe_audio"):
            text = self._transcribe_gemini(audio)
            if text and is_valid_human_transcription(text):
                self.last_detected_language = detect_language_code(text, "pt")
                return text, f"Gemini-Poliglota ({self.last_detected_language})"

        text = self._transcribe_https_l16(audio) or self._transcribe_google_https(audio) or self._transcribe_gemini(audio)
        if text and is_valid_human_transcription(text):
            self.last_detected_language = detect_language_code(text, mode if mode != "auto" else "pt")
            return text, f"Google-HTTPS ({self.last_detected_language})"
        return None, "None"

    def _transcribe_https_l16(self, audio: sr.AudioData) -> str | None:
        try:
            raw_pcm = audio.get_raw_data(convert_rate=16000, convert_width=2)
            params = urlencode({"client": "chromium", "lang": self._language, "key": CHROMIUM_KEY, "pFilter": 0})
            req = urllib.request.Request(
                f"{HTTPS_SPEECH_ENDPOINT}?{params}",
                data=raw_pcm,
                headers={"Content-Type": "audio/l16; rate=16000", "User-Agent": CHROME_USER_AGENT},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=3.2) as resp:
                return self._parse_chromium_json(resp.read().decode("utf-8", errors="ignore"))
        except Exception:
            return None

    def _transcribe_google_https(self, audio: sr.AudioData) -> str | None:
        try:
            self._recognizer.operation_timeout = 3.2
            res = self._recognizer.recognize_google(audio, language=self._language, endpoint=HTTPS_SPEECH_ENDPOINT)
            return str(res).strip() or None
        except Exception:
            return None

    def _transcribe_gemini(self, audio: sr.AudioData) -> str | None:
        if not self._gemini or not hasattr(self._gemini, "transcribe_audio"):
            return None
        try:
            return self._gemini.transcribe_audio(audio.get_wav_data(convert_rate=16000, convert_width=2))
        except Exception:
            return None

    @staticmethod
    def _parse_chromium_json(response_text: str) -> str | None:
        for line in response_text.splitlines():
            try:
                results = json.loads(line.strip()).get("result", [])
                if results and results[0].get("alternative"):
                    transcript = str(results[0]["alternative"][0].get("transcript", "")).strip()
                    if transcript:
                        return transcript
            except Exception:
                continue
        return None
