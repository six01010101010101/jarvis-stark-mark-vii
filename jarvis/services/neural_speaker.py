"""Motor de voz neural limpa (Edge-TTS pt-BR-AntonioNeural) com fila de streaming por frases e GPU."""

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
GPU_DEVICE = "cuda"
GPU_COMPUTE_TYPE = "float16"

THINKING_FILLERS = (
    "Analisando os dados, senhor...",
    "Consultando a rede, só um instante...",
    "Processando os parâmetros, senhor.",
    "Um momento enquanto processo isso...",
)


def split_into_chunks(text: str) -> list[str]:
    """Quebra o texto em frases curtas por pontuação (., !, ?, :, ;) para reprodução imediata."""
    chunks = re.split(r"(?<=[.!?।:;])\s+", text.strip())
    return [c.strip() for c in chunks if c.strip()]


def _pump_win32_messages() -> None:
    try:
        user32 = ctypes.windll.user32
        msg = ctypes.wintypes.MSG()
        while user32.PeekMessageW(ctypes.byref(msg), 0, 0, 0, 1):
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
    except Exception:
        pass


def _play_mp3_native(mp3_path: Path, max_wait: float = 16.0) -> bool:
    """Reproduz arquivo MP3 nativamente no Windows (WMPlayer COM + MCI fallback)."""
    if not mp3_path.exists() or mp3_path.stat().st_size == 0:
        return False
    est_duration = max(0.7, min((mp3_path.stat().st_size / 5800.0) + 0.4, max_wait))
    try:
        import comtypes
        comtypes.CoInitialize()
        import comtypes.client
        wmp = comtypes.client.CreateObject("WMPlayer.OCX")
        wmp.settings.volume = 100
        media = wmp.newMedia(str(mp3_path.resolve()))
        wmp.currentMedia = media
        wmp.controls.play()
        t_start = time.time()
        started = False
        while time.time() - t_start < 1.1:
            _pump_win32_messages()
            if wmp.playState == 3:
                started = True
                break
            time.sleep(0.02)
        if started:
            t0 = time.time()
            while time.time() - t0 < est_duration:
                _pump_win32_messages()
                if wmp.playState in (1, 8):
                    break
                dur = float(getattr(media, "duration", 0.0) or 0.0)
                pos = float(getattr(wmp.controls, "currentPosition", 0.0) or 0.0)
                if dur > 0.2 and pos >= dur - 0.06:
                    break
                time.sleep(0.025)
            wmp.controls.stop()
            wmp.close()
            return True
        wmp.controls.stop()
        wmp.close()
    except Exception:
        pass

    try:
        buf = ctypes.create_unicode_buffer(300)
        ctypes.windll.kernel32.GetShortPathNameW(str(mp3_path), buf, 300)
        short_path = buf.value or str(mp3_path)
        alias = f"jarvis_mci_{int(time.time() * 1000)}"
        winmm = ctypes.windll.winmm
        if winmm.mciSendStringW(f'open "{short_path}" alias {alias}', None, 0, 0) == 0:
            winmm.mciSendStringW(f"play {alias}", None, 0, 0)
            t0 = time.time()
            while time.time() - t0 < est_duration:
                _pump_win32_messages()
                status = ctypes.create_unicode_buffer(64)
                winmm.mciSendStringW(f"status {alias} mode", status, 64, 0)
                if time.time() - t0 > 0.3 and "playing" not in status.value.lower():
                    break
                time.sleep(0.025)
            winmm.mciSendStringW(f"stop {alias}", None, 0, 0)
            winmm.mciSendStringW(f"close {alias}", None, 0, 0)
            return True
    except Exception:
        pass
    return False


class NeuralSpeakerStream:
    """Fila de áudio por sentenças: reproduz a 1ª frase em < 1.5s enquanto sintetiza o resto."""

    def __init__(self, tts_engine: object) -> None:
        self.tts_engine = tts_engine
        self.audio_queue: queue.Queue[tuple[str, Callable[[], None] | None]] = queue.Queue()
        self.is_speaking = False
        self._stop_event = threading.Event()
        self._worker_thread = threading.Thread(target=self._playback_loop, name="neural-stream", daemon=True)
        self._worker_thread.start()

    def split_into_chunks(self, text: str) -> list[str]:
        return split_into_chunks(text)

    def speak_async(self, text: str, on_complete: Callable[[], None] | None = None) -> None:
        self._stop_event.clear()
        chunks = self.split_into_chunks(text)
        for i, chunk in enumerate(chunks):
            is_last = i == len(chunks) - 1
            self.audio_queue.put((chunk, on_complete if is_last else None))

    def speak_thinking_filler(self) -> None:
        self.speak_async(random.choice(THINKING_FILLERS))

    def _playback_loop(self) -> None:
        while True:
            chunk, callback = self.audio_queue.get()
            if self._stop_event.is_set():
                self.audio_queue.task_done()
                continue
            try:
                self.is_speaking = True
                if hasattr(self.tts_engine, "say_chunk"):
                    self.tts_engine.say_chunk(chunk)  # type: ignore[attr-defined]
                elif hasattr(self.tts_engine, "speak"):
                    self.tts_engine.speak(chunk)  # type: ignore[attr-defined]
                elif hasattr(self.tts_engine, "say"):
                    self.tts_engine.say(chunk)  # type: ignore[attr-defined]
            except Exception as exc:
                logger.debug("Erro no NeuralSpeakerStream: %s", exc)
            finally:
                self.audio_queue.task_done()
                if self.audio_queue.empty():
                    self.is_speaking = False
                if callback:
                    callback()


class NeuralSpeaker(Speaker):
    """Sintetizador com streaming por sentenças, pré-síntese paralela e aceleração GPU."""

    def __init__(self, fallback: Speaker, on_start: Callable[[], None], on_end: Callable[[], None]) -> None:
        self._fallback = fallback
        self._on_start = on_start
        self._on_end = on_end
        self._lock = threading.Lock()
        self._profile = "male"
        self._voice = DEFAULT_MALE_VOICE
        self.device = GPU_DEVICE
        self.compute_type = GPU_COMPUTE_TYPE
        self.is_speaking = False
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self._stream = NeuralSpeakerStream(self)

    def set_voice(self, profile: str) -> bool:
        p = profile.lower()
        if any(w in p for w in ("cinema", "ryan", "paul", "bettany", "ingles", "english")):
            self._profile, self._voice = "cinema", "en-GB-RyanNeural"
        elif any(w in p for w in ("fem", "maria", "mulher", "francisca")):
            self._profile, self._voice = "female", DEFAULT_FEMALE_VOICE
        else:
            self._profile, self._voice = "male", DEFAULT_MALE_VOICE
        if hasattr(self._fallback, "set_voice"):
            self._fallback.set_voice(self._profile)
        return True

    def get_voice(self) -> str:
        if self._voice == DEFAULT_MALE_VOICE:
            return f"Neural Jarvis ({DEFAULT_MALE_VOICE})"
        if self._voice == "en-GB-RyanNeural":
            return "Neural Cinema (en-GB-RyanNeural / Paul Bettany)"
        return f"Neural Feminina ({DEFAULT_FEMALE_VOICE})"

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
        except Exception:
            return False

    def say_chunk(self, chunk: str) -> None:
        cached = self._get_cache_path(chunk)
        played = False
        if cached.exists() and cached.stat().st_size > 0:
            played = _play_mp3_native(cached)
        elif self._synthesize_edge(chunk, cached):
            played = _play_mp3_native(cached)
        if not played:
            self._fallback.say(chunk)

    def say(self, text: str) -> None:
        """Divide em sentenças: reproduz a 1ª imediatamente enquanto sintetiza as demais em background."""
        clean = text.strip()
        if not clean:
            return
        chunks = split_into_chunks(clean)
        if not chunks:
            return

        if len(chunks) > 1:
            def _prefetch(rest: list[str]) -> None:
                for ch in rest:
                    self._synthesize_edge(ch, self._get_cache_path(ch))
            threading.Thread(target=_prefetch, args=(chunks[1:],), daemon=True).start()

        with self._lock:
            self.is_speaking = True
            self._on_start()
            try:
                for chunk in chunks:
                    self.say_chunk(chunk)
            finally:
                self.is_speaking = False
                self._on_end()

    def speak_async(self, text: str, on_complete: Callable[[], None] | None = None) -> None:
        self._stream.speak_async(text, on_complete=on_complete)

    def speak_thinking_filler(self) -> None:
        threading.Thread(target=self.say, args=(random.choice(THINKING_FILLERS),), daemon=True).start()
