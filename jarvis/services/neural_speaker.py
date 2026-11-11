"""Motor de voz neural limpa do J.A.R.V.I.S. (pt-BR-AntonioNeural) com parada instantânea e cache."""

from __future__ import annotations

import asyncio
import ctypes
import hashlib
import logging
from pathlib import Path
import queue
import random
import re
import threading
import time
from typing import Callable

from jarvis.contracts import Speaker
from jarvis.speech.native_player import play_mp3_native

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "jarvis_sounds" / "tts_cache"
DEFAULT_MALE_VOICE = "pt-BR-AntonioNeural"
DEFAULT_FEMALE_VOICE = "pt-BR-FranciscaNeural"

LANGUAGE_VOICES: dict[str, str] = {
    "pt": "pt-BR-AntonioNeural", "en": "en-GB-RyanNeural", "es": "es-ES-AlvaroNeural",
    "ja": "ja-JP-KeitaNeural", "fr": "fr-FR-HenriNeural", "de": "de-DE-ConradNeural", "it": "it-IT-DiegoNeural",
}

THINKING_FILLERS = (
    "Analisando os dados, senhor.", "Consultando a rede, só um instante.", "Processando os parâmetros, senhor.",
)


def split_into_chunks(text: str) -> list[str]:
    return [c.strip() for c in re.split(r"(?<=[.!?।:;])\s+", str(text or "").strip()) if c.strip()]


class SafeNeuralSpeaker:
    """Executor assíncrono para chamadas de fala sem bloquear a UI."""

    def __init__(self, tts_engine: object) -> None:
        self.tts_engine = tts_engine
        self.audio_queue: queue.Queue[tuple[str, Callable[[], None] | None]] = queue.Queue()
        self.is_speaking = False

    def speak_async(self, text: str, lang: str = "pt", on_complete: Callable[[], None] | None = None) -> None:
        def _worker() -> None:
            self.is_speaking = True
            try:
                getattr(self.tts_engine, "say")(text)
            finally:
                self.is_speaking = False
                if on_complete:
                    on_complete()
        threading.Thread(target=_worker, name="tts-async", daemon=True).start()


NeuralSpeakerStream = SafeNeuralSpeaker


class NeuralSpeaker(Speaker):
    """Sintetizador oficial do Jarvis (voz masculina pt-BR-AntonioNeural) com parada instantânea."""

    def __init__(self, fallback: Speaker, on_start: Callable[[], None], on_end: Callable[[], None]) -> None:
        self._fallback, self._on_start, self._on_end = fallback, on_start, on_end
        self._lock = threading.Lock()
        self._profile, self._voice = "male", DEFAULT_MALE_VOICE
        self.is_speaking = False
        self._stop_event = threading.Event()
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self._stream = SafeNeuralSpeaker(self)

    def stop(self) -> None:
        """Interrompe qualquer reprodução de voz imediatamente ('Jarvis, pare')."""
        self._stop_event.set()
        try:
            ctypes.windll.winmm.mciSendStringW("stop all", None, 0, 0)
            ctypes.windll.winmm.mciSendStringW("close all", None, 0, 0)
        except Exception:
            pass
        if hasattr(self._fallback, "stop"):
            self._fallback.stop()

    def set_voice(self, profile: str) -> bool:
        p = profile.lower()
        code = p.split("-")[0] if "-" in p else p
        if code in LANGUAGE_VOICES:
            self._profile, self._voice = code, LANGUAGE_VOICES[code]
        elif any(w in p for w in ("cinema", "ryan", "paul", "bettany", "ingles", "english")):
            self._profile, self._voice = "cinema", "en-GB-RyanNeural"
        elif any(w in p for w in ("fem", "maria", "mulher", "francisca")):
            self._profile, self._voice = "female", DEFAULT_FEMALE_VOICE
        else:
            self._profile, self._voice = "male", DEFAULT_MALE_VOICE
        if hasattr(self._fallback, "set_voice"):
            self._fallback.set_voice(self._profile)
        return True

    def set_language_voice(self, lang_code: str) -> str:
        code = lang_code.split("-")[0].lower() if "-" in lang_code else lang_code.lower()
        if code in LANGUAGE_VOICES:
            self._voice = LANGUAGE_VOICES[code]
        return self._voice

    def get_voice(self) -> str:
        if self._voice == DEFAULT_MALE_VOICE:
            return f"Neural Jarvis ({DEFAULT_MALE_VOICE})"
        if self._voice == DEFAULT_FEMALE_VOICE or self._profile == "female":
            return f"Neural Feminina ({DEFAULT_FEMALE_VOICE})"
        if self._voice == "en-GB-RyanNeural":
            return "Neural Cinema (en-GB-RyanNeural / Paul Bettany)"
        return f"Neural Poliglota ({self._voice})"

    def _get_cache_path(self, text: str) -> Path:
        digest = hashlib.md5(f"{self._voice}_{text.strip()}".encode("utf-8")).hexdigest()[:16]
        return CACHE_DIR / f"tts_{digest}.mp3"

    def _synthesize_edge(self, text: str, out_path: Path) -> bool:
        if out_path.exists() and out_path.stat().st_size > 0:
            return True
        async def _run() -> None:
            import edge_tts
            await edge_tts.Communicate(text, self._voice, rate="+8%").save(str(out_path))
        for _ in range(3):
            loop = asyncio.new_event_loop()
            try:
                loop.run_until_complete(asyncio.wait_for(_run(), timeout=6.5))
                if out_path.exists() and out_path.stat().st_size > 0:
                    return True
            except Exception:
                time.sleep(0.1)
            finally:
                loop.close()
        return False

    def say(self, text: str) -> None:
        clean = text.strip()
        if not clean:
            return
        with self._lock:
            self.is_speaking, played = True, False
            self._stop_event.clear()
            cached_file = self._get_cache_path(clean)
            self._on_start()
            try:
                if not self._stop_event.is_set() and cached_file.exists() and cached_file.stat().st_size > 0:
                    played = play_mp3_native(cached_file, stop_event=self._stop_event)
                if not played and not self._stop_event.is_set() and self._synthesize_edge(clean, cached_file):
                    played = play_mp3_native(cached_file, stop_event=self._stop_event)
                if not played and not self._stop_event.is_set():
                    self._fallback.say(clean)
            finally:
                self.is_speaking = False
                self._on_end()

    def speak_async(self, text: str, on_complete: Callable[[], None] | None = None) -> None:
        self._stream.speak_async(text, on_complete=on_complete)

    def speak_thinking_filler(self) -> None:
        threading.Thread(target=self.say, args=(random.choice(THINKING_FILLERS),), daemon=True).start()
