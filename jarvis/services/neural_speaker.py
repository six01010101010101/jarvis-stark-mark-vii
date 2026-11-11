"""Motor de voz neural blindado (SafeNeuralSpeaker + Edge-TTS + SAPI5 COM Thread Init)."""

from __future__ import annotations

import asyncio
import ctypes
import ctypes.wintypes
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

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "jarvis_sounds" / "tts_cache"
DEFAULT_MALE_VOICE = "pt-BR-AntonioNeural"
DEFAULT_FEMALE_VOICE = "pt-BR-FranciscaNeural"
GPU_DEVICE, GPU_COMPUTE_TYPE = "cuda", "float16"

LANGUAGE_VOICES: dict[str, str] = {
    "pt": "pt-BR-AntonioNeural", "en": "en-GB-RyanNeural", "es": "es-ES-AlvaroNeural",
    "ja": "ja-JP-KeitaNeural", "fr": "fr-FR-HenriNeural", "de": "de-DE-ConradNeural", "it": "it-IT-DiegoNeural",
}

THINKING_FILLERS = (
    "Analisando os dados, senhor...", "Consultando a rede, só um instante...",
    "Processando os parâmetros, senhor.", "Um momento enquanto processo isso...",
)


def split_into_chunks(text: str) -> list[str]:
    if not text or not str(text).strip():
        return []
    return [c.strip() for c in re.split(r"(?<=[.!?।:;])\s+", str(text).strip()) if c.strip()]


def _init_windows_com_in_thread() -> None:
    """Inicializa COM no Windows para que SAPI5/WMPlayer nunca fiquem mudos em threads secundárias."""
    try:
        import pythoncom  # type: ignore[import-not-found]
        pythoncom.CoInitialize()
        return
    except Exception:
        pass
    try:
        import comtypes
        comtypes.CoInitialize()
    except Exception:
        pass


def _pump_win32_messages() -> None:
    try:
        user32, msg = ctypes.windll.user32, ctypes.wintypes.MSG()
        while user32.PeekMessageW(ctypes.byref(msg), 0, 0, 0, 1):
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
    except Exception:
        pass


def _play_mp3_native(mp3_path: Path, max_wait: float = 16.0) -> bool:
    if not mp3_path.exists() or mp3_path.stat().st_size == 0:
        return False
    _init_windows_com_in_thread()
    est_duration = max(0.7, min((mp3_path.stat().st_size / 5800.0) + 0.4, max_wait))
    try:
        import comtypes.client
        wmp = comtypes.client.CreateObject("WMPlayer.OCX")
        wmp.settings.volume = 100
        media = wmp.newMedia(str(mp3_path.resolve()))
        wmp.currentMedia = media
        wmp.controls.play()
        t_start = time.time()
        while time.time() - t_start < 1.1:
            _pump_win32_messages()
            if wmp.playState == 3:
                t0 = time.time()
                while time.time() - t0 < est_duration:
                    _pump_win32_messages()
                    dur = float(getattr(media, "duration", 0.0) or 0.0)
                    pos = float(getattr(wmp.controls, "currentPosition", 0.0) or 0.0)
                    if wmp.playState in (1, 8) or (dur > 0.2 and pos >= dur - 0.06):
                        break
                    time.sleep(0.025)
                wmp.controls.stop()
                wmp.close()
                return True
            time.sleep(0.02)
        wmp.controls.stop()
        wmp.close()
    except Exception as exc:
        logger.debug("WMPlayer.OCX fallback acionado: %s", exc)
    return False


class SafeNeuralSpeaker:
    """Motor de fala blindado contra falhas de Thread (COM / Asyncio) no Windows."""

    def __init__(self, tts_engine: object) -> None:
        self.tts_engine = tts_engine
        self.audio_queue: queue.Queue[tuple[str, str, Callable[[], None] | None]] = queue.Queue()
        self.is_speaking = False
        self._stop_event = threading.Event()
        self._worker = threading.Thread(target=self._playback_worker, name="safe-neural-tts", daemon=True)
        self._worker.start()

    def split_into_chunks(self, text: str) -> list[str]:
        return split_into_chunks(text)

    def speak(self, text: str, lang: str = "pt", on_done: Callable[[], None] | None = None) -> None:
        self.speak_async(text, lang=lang, on_complete=on_done)

    def speak_async(self, text: str, lang: str = "pt", on_complete: Callable[[], None] | None = None) -> None:
        chunks = split_into_chunks(text)
        if not chunks:
            if on_complete:
                on_complete()
            return
        self._stop_event.clear()
        for i, chunk in enumerate(chunks):
            self.audio_queue.put((chunk, lang, on_complete if i == len(chunks) - 1 else None))

    def speak_thinking_filler(self) -> None:
        self.speak_async(random.choice(THINKING_FILLERS))

    def _playback_worker(self) -> None:
        _init_windows_com_in_thread()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        while True:
            chunk, lang, callback = self.audio_queue.get()
            if not self._stop_event.is_set():
                try:
                    self.is_speaking = True
                    print(f"[JARVIS FALANDO ({lang})]: {chunk}", flush=True)
                    if hasattr(self.tts_engine, "say_chunk"):
                        self.tts_engine.say_chunk(chunk)  # type: ignore[attr-defined]
                    elif hasattr(self.tts_engine, "say"):
                        self.tts_engine.say(chunk)  # type: ignore[attr-defined]
                    elif callable(self.tts_engine):
                        self.tts_engine(chunk)
                except Exception as exc:
                    print(f"[ERRO CRÍTICO TTS RECUPERADO]: {exc}", flush=True)
            self.audio_queue.task_done()
            if self.audio_queue.empty():
                self.is_speaking = False
            if callback:
                try:
                    callback()
                except Exception as cb_err:
                    print(f"[ERRO CALLBACK PÓS-FALA]: {cb_err}", flush=True)


NeuralSpeakerStream = SafeNeuralSpeaker


class NeuralSpeaker(Speaker):
    """Sintetizador Poliglota com streaming por sentenças, inicialização COM e fallback SAPI5."""

    def __init__(self, fallback: Speaker, on_start: Callable[[], None], on_end: Callable[[], None]) -> None:
        self._fallback, self._on_start, self._on_end = fallback, on_start, on_end
        self._lock = threading.Lock()
        self._profile, self._voice = "male", DEFAULT_MALE_VOICE
        self.device, self.compute_type = GPU_DEVICE, GPU_COMPUTE_TYPE
        self.is_speaking = False
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self._stream = SafeNeuralSpeaker(self)

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
        if self._voice == "en-GB-RyanNeural":
            return "Neural Cinema (en-GB-RyanNeural / Paul Bettany)"
        return f"Neural Feminina ({DEFAULT_FEMALE_VOICE})" if self._voice == DEFAULT_FEMALE_VOICE else f"Neural Poliglota ({self._voice})"

    def _get_cache_path(self, text: str) -> Path:
        digest = hashlib.md5(f"{self._voice}_{text.strip()}".encode("utf-8")).hexdigest()[:16]
        return CACHE_DIR / f"tts_{digest}.mp3"

    def _synthesize_edge(self, text: str, out_path: Path) -> bool:
        if out_path.exists() and out_path.stat().st_size > 0:
            return True
        async def _run() -> None:
            import edge_tts
            await edge_tts.Communicate(text, self._voice, rate="-2%").save(str(out_path))
        try:
            loop = asyncio.new_event_loop()
            try:
                loop.run_until_complete(asyncio.wait_for(_run(), timeout=3.2))
                return out_path.exists() and out_path.stat().st_size > 0
            finally:
                loop.close()
        except Exception as exc:
            logger.debug("Síntese Edge-TTS falhou (%s); usando SAPI5 nativo.", exc)
            return False

    def say_chunk(self, chunk: str) -> None:
        _init_windows_com_in_thread()
        print(f"[JARVIS FALANDO ({self._profile})]: {chunk}", flush=True)
        cached = self._get_cache_path(chunk)
        played = _play_mp3_native(cached) if (cached.exists() and cached.stat().st_size > 0) else (
            _play_mp3_native(cached) if self._synthesize_edge(chunk, cached) else False
        )
        if not played:
            self._fallback.say(chunk)

    def say(self, text: str) -> None:
        chunks = split_into_chunks(text)
        if not chunks:
            return
        if len(chunks) > 1:
            threading.Thread(target=lambda r: [self._synthesize_edge(c, self._get_cache_path(c)) for c in r], args=(chunks[1:],), daemon=True).start()
        with self._lock:
            self.is_speaking = True
            self._on_start()
            try:
                for chunk in chunks:
                    self.say_chunk(chunk)
            except Exception as exc:
                print(f"[ERRO CRÍTICO TTS RECUPERADO]: {exc}", flush=True)
                self._fallback.say(text)
            finally:
                self.is_speaking = False
                self._on_end()

    def speak_async(self, text: str, on_complete: Callable[[], None] | None = None) -> None:
        self._stream.speak_async(text, lang=self._profile, on_complete=on_complete)

    def speak_thinking_filler(self) -> None:
        threading.Thread(target=self.say, args=(random.choice(THINKING_FILLERS),), daemon=True).start()
