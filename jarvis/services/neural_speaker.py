"""Motor de voz neural limpa do J.A.R.V.I.S. (pt-BR-AntonioNeural) com reprodução acelerada e cache."""

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

LANGUAGE_VOICES: dict[str, str] = {
    "pt": "pt-BR-AntonioNeural", "en": "en-GB-RyanNeural", "es": "es-ES-AlvaroNeural",
    "ja": "ja-JP-KeitaNeural", "fr": "fr-FR-HenriNeural", "de": "de-DE-ConradNeural", "it": "it-IT-DiegoNeural",
}

THINKING_FILLERS = (
    "Analisando os dados, senhor.",
    "Consultando a rede, só um instante.",
    "Processando os parâmetros, senhor.",
)


def split_into_chunks(text: str) -> list[str]:
    if not text or not str(text).strip():
        return []
    return [c.strip() for c in re.split(r"(?<=[.!?।:;])\s+", str(text).strip()) if c.strip()]


def _pump_win32_messages() -> None:
    try:
        user32, msg = ctypes.windll.user32, ctypes.wintypes.MSG()
        while user32.PeekMessageW(ctypes.byref(msg), 0, 0, 0, 1):
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
    except Exception:
        pass


def _play_mp3_native(mp3_path: Path, max_wait: float = 16.0) -> bool:
    """Reproduz arquivo MP3 da voz masculina do Jarvis (WMPlayer COM 1.14x + MCI fallback)."""
    if not mp3_path.exists() or mp3_path.stat().st_size == 0:
        return False
    est_duration = max(0.55, min((mp3_path.stat().st_size / 6600.0) + 0.25, max_wait))
    try:
        import comtypes
        import comtypes.client
        comtypes.CoInitialize()
        wmp = comtypes.client.CreateObject("WMPlayer.OCX")
        wmp.settings.volume = 100
        try:
            wmp.settings.rate = 1.14
        except Exception:
            pass
        media = wmp.newMedia(str(mp3_path.resolve()))
        wmp.currentMedia = media
        wmp.controls.play()
        started, t_start = False, time.time()
        while time.time() - t_start < 1.2:
            _pump_win32_messages()
            if wmp.playState == 3:
                started = True
                break
            time.sleep(0.015)
        if started:
            t0 = time.time()
            while time.time() - t0 < est_duration:
                _pump_win32_messages()
                if wmp.playState in (1, 8):
                    break
                dur = float(getattr(media, "duration", 0.0) or 0.0)
                pos = float(getattr(wmp.controls, "currentPosition", 0.0) or 0.0)
                if dur > 0.15 and pos >= dur - 0.04:
                    break
                time.sleep(0.015)
            wmp.controls.stop()
            wmp.close()
            return True
        wmp.controls.stop()
        wmp.close()
    except Exception as exc:
        logger.debug("Falha WMPlayer.OCX: %s", exc)

    try:
        buf = ctypes.create_unicode_buffer(300)
        ctypes.windll.kernel32.GetShortPathNameW(str(mp3_path), buf, 300)
        short_path = buf.value or str(mp3_path)
        alias = f"jarvis_mci_{int(time.time() * 1000)}"
        winmm = ctypes.windll.winmm
        res = winmm.mciSendStringW(f'open "{short_path}" type mpegvideo alias {alias}', None, 0, 0)
        if res != 0:
            res = winmm.mciSendStringW(f'open "{short_path}" alias {alias}', None, 0, 0)
        if res == 0:
            winmm.mciSendStringW(f"play {alias}", None, 0, 0)
            t0 = time.time()
            while time.time() - t0 < est_duration + 0.3:
                _pump_win32_messages()
                status = ctypes.create_unicode_buffer(64)
                winmm.mciSendStringW(f"status {alias} mode", status, 64, 0)
                if time.time() - t0 > 0.25 and "playing" not in status.value.lower():
                    break
                time.sleep(0.015)
            winmm.mciSendStringW(f"stop {alias}", None, 0, 0)
            winmm.mciSendStringW(f"close {alias}", None, 0, 0)
            return True
    except Exception as exc:
        logger.debug("Falha MCI: %s", exc)
    return False


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
    """Sintetizador oficial do Jarvis (voz masculina pt-BR-AntonioNeural) com cache instantâneo."""

    def __init__(self, fallback: Speaker, on_start: Callable[[], None], on_end: Callable[[], None]) -> None:
        self._fallback, self._on_start, self._on_end = fallback, on_start, on_end
        self._lock = threading.Lock()
        self._profile, self._voice = "male", DEFAULT_MALE_VOICE
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
            cached_file = self._get_cache_path(clean)
            self._on_start()
            try:
                if cached_file.exists() and cached_file.stat().st_size > 0:
                    played = _play_mp3_native(cached_file)
                if not played and self._synthesize_edge(clean, cached_file):
                    played = _play_mp3_native(cached_file)
                if not played:
                    self._fallback.say(clean)
            finally:
                self.is_speaking = False
                self._on_end()

    def speak_async(self, text: str, on_complete: Callable[[], None] | None = None) -> None:
        self._stream.speak_async(text, on_complete=on_complete)

    def speak_thinking_filler(self) -> None:
        threading.Thread(target=self.say, args=(random.choice(THINKING_FILLERS),), daemon=True).start()
