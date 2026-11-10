"""Motor de transcrição multicamada (GPU CUDA Faster-Whisper + HTTPS L16 Direto + Google STT + Gemini)."""

from __future__ import annotations

import io
import json
import logging
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


class MultiEngineTranscriber:
    """Converte áudio capturado em texto priorizando GPU CUDA (RTX 4060) e HTTPS Direto."""

    def __init__(
        self,
        recognizer: sr.Recognizer,
        language: str = "pt-BR",
        gemini: object | None = None,
        device: str = "cuda",
        compute_type: str = "float16",
    ) -> None:
        self._recognizer = recognizer
        self._language = language
        self._gemini = gemini
        self.device = device
        self.compute_type = compute_type
        self._gpu_model: object | None = None
        self._init_gpu_accelerator()

    def _init_gpu_accelerator(self) -> None:
        """Inicializa aceleração de hardware GPU (CUDA / float16 para RTX 4060) se Faster-Whisper estiver presente."""
        try:
            from faster_whisper import WhisperModel  # type: ignore[import-not-found]
            self._gpu_model = WhisperModel("small", device=self.device, compute_type=self.compute_type)
            logger.info("⚡ [GPU-STT] Faster-Whisper ativado na RTX (%s / %s).", self.device, self.compute_type)
        except Exception:
            self._gpu_model = None

    def transcribe(self, audio: sr.AudioData) -> tuple[str | None, str]:
        """Tenta transcrever o áudio através de múltiplas camadas de baixa latência."""
        if self._gpu_model is not None:
            text = self._transcribe_cuda_whisper(audio)
            if text:
                return text, "GPU-CUDA-Float16"

        # Camada 1: HTTPS Direto com PCM L16 16kHz e User-Agent Chrome
        text = self._transcribe_https_l16(audio)
        if text:
            return text, "Google-HTTPS-Direct"

        # Camada 2: Recognizer Google via endpoint HTTPS explícito
        text = self._transcribe_google_https(audio)
        if text:
            return text, "Google-STT"

        # Camada 3: Gemini Audio API Autenticada
        text = self._transcribe_gemini(audio)
        if text:
            return text, "Gemini-Neural"

        return None, "None"

    def _transcribe_cuda_whisper(self, audio: sr.AudioData) -> str | None:
        if self._gpu_model is None:
            return None
        try:
            wav_bytes = audio.get_wav_data(convert_rate=16000, convert_width=2)
            segments, _ = self._gpu_model.transcribe(  # type: ignore[attr-defined]
                io.BytesIO(wav_bytes),
                language="pt",
                beam_size=1,
                vad_filter=True,
            )
            joined = " ".join(seg.text.strip() for seg in segments).strip()
            return joined if joined else None
        except Exception as exc:
            logger.debug("Camada GPU CUDA falhou: %s", exc)
            return None

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
            with urllib.request.urlopen(req, timeout=3.2) as resp:
                body = resp.read().decode("utf-8", errors="ignore")
            return self._parse_chromium_json(body)
        except Exception as exc:
            logger.debug("Camada 1 (HTTPS L16) falhou: %s", exc)
            return None

    def _transcribe_google_https(self, audio: sr.AudioData) -> str | None:
        try:
            self._recognizer.operation_timeout = 3.2
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
