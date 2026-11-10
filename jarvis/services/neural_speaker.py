"""Motor de voz neural limpa (Edge-TTS pt-BR-AntonioNeural) com reprodução de baixa latência e fallback offline."""

from __future__ import annotations

import asyncio
import ctypes
import ctypes.wintypes
import hashlib
import logging
import threading
import time
from pathlib import Path
from typing import Callable

from jarvis.contracts import Speaker

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "jarvis_sounds" / "tts_cache"
DEFAULT_MALE_VOICE = "pt-BR-AntonioNeural"
DEFAULT_FEMALE_VOICE = "pt-BR-FranciscaNeural"


def _pump_win32_messages() -> None:
    """Processa mensagens Win32 da thread atual para destravar eventos COM/WMPlayer/MCI."""
    try:
        user32 = ctypes.windll.user32
        msg = ctypes.wintypes.MSG()
        while user32.PeekMessageW(ctypes.byref(msg), 0, 0, 0, 1):
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
    except Exception:
        pass


def _play_mp3_native(mp3_path: Path, max_wait: float = 18.0) -> bool:
    """Reproduz arquivo MP3 nativamente no Windows com múltiplas camadas (WMPlayer + MCI)."""
    if not mp3_path.exists() or mp3_path.stat().st_size == 0:
        return False

    file_size = mp3_path.stat().st_size
    est_duration = max(0.8, min((file_size / 5800.0) + 0.45, max_wait))

    # 1. Tenta reproduzir via Windows Media Player COM (nativo do Windows)
    try:
        import comtypes
        comtypes.CoInitialize()
        import comtypes.client
        wmp = comtypes.client.CreateObject("WMPlayer.OCX")
        wmp.settings.volume = 100
        media = wmp.newMedia(str(mp3_path.resolve()))
        wmp.currentMedia = media
        wmp.controls.play()
        started = False
        t_start = time.time()
        while time.time() - t_start < 1.2:
            _pump_win32_messages()
            if wmp.playState == 3:  # Playing
                started = True
                break
            time.sleep(0.025)

        if started:
            t0 = time.time()
            while time.time() - t0 < est_duration:
                _pump_win32_messages()
                if wmp.playState in (1, 8):  # 1 = Stopped, 8 = MediaEnded
                    break
                dur = float(getattr(media, "duration", 0.0) or 0.0)
                pos = float(getattr(wmp.controls, "currentPosition", 0.0) or 0.0)
                if dur > 0.2 and pos >= dur - 0.08:
                    break
                time.sleep(0.03)
            wmp.controls.stop()
            wmp.close()
            return True
        wmp.controls.stop()
        wmp.close()
    except Exception as exc:
        logger.debug("Falha na reprodução WMPlayer.OCX: %s", exc)

    # 2. Camada secundária: MCI com short path 8.3
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
            while time.time() - t0 < est_duration:
                _pump_win32_messages()
                status = ctypes.create_unicode_buffer(64)
                winmm.mciSendStringW(f"status {alias} mode", status, 64, 0)
                mode = status.value.lower().strip()
                if time.time() - t0 > 0.35 and mode and "playing" not in mode:
                    break
                time.sleep(0.03)
            winmm.mciSendStringW(f"stop {alias}", None, 0, 0)
            winmm.mciSendStringW(f"close {alias}", None, 0, 0)
            return True
    except Exception as exc:
        logger.debug("Falha na reprodução nativa MCI: %s", exc)

    return False


class NeuralSpeaker(Speaker):
    """Sintetizador com voz humana ultra-limpa e transição transparente para o motor nativo."""

    def __init__(
        self,
        fallback: Speaker,
        on_start: Callable[[], None],
        on_end: Callable[[], None],
    ) -> None:
        self._fallback = fallback
        self._on_start = on_start
        self._on_end = on_end
        self._lock = threading.Lock()
        self._profile = "male"
        self._voice = DEFAULT_MALE_VOICE
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def set_voice(self, profile: str) -> bool:
        """Alterna entre voz masculina (Antonio/Jarvis), cinema (Ryan) e feminina (Francisca)."""
        p = profile.lower()
        if any(w in p for w in ("cinema", "ryan", "paul", "bettany", "ingles", "english")):
            self._profile = "cinema"
            self._voice = "en-GB-RyanNeural"
        elif any(w in p for w in ("fem", "maria", "mulher", "francisca")):
            self._profile = "female"
            self._voice = DEFAULT_FEMALE_VOICE
        else:
            self._profile = "male"
            self._voice = DEFAULT_MALE_VOICE

        if hasattr(self._fallback, "set_voice"):
            self._fallback.set_voice(self._profile)
        logger.info("🎙️ [TTS-NEURAL] Voz definida para: %s (%s)", self._voice, self._profile)
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
        """Gera áudio através do Edge-TTS em thread limpa isolada."""
        async def _run() -> None:
            import edge_tts
            communicate = edge_tts.Communicate(text, self._voice, rate="-3%")
            await communicate.save(str(out_path))

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(asyncio.wait_for(_run(), timeout=3.8))
                return out_path.exists() and out_path.stat().st_size > 0
            finally:
                loop.close()
        except Exception as exc:
            logger.debug("Edge-TTS indisponível ou timeout (%s). Utilizando sintetizador nativo.", exc)
            return False

    def say(self, text: str) -> None:
        """Sintetiza e reproduz voz limpa com fallback automático instantâneo."""
        clean = text.strip()
        if not clean:
            return

        with self._lock:
            cached_file = self._get_cache_path(clean)
            played = False

            self._on_start()
            try:
                if cached_file.exists() and cached_file.stat().st_size > 0:
                    played = _play_mp3_native(cached_file)

                if not played:
                    if self._synthesize_edge(clean, cached_file):
                        played = _play_mp3_native(cached_file)

                if not played:
                    logger.info("🎙️ [TTS] Usando motor de fala nativo para '%s'...", clean[:30])
                    self._fallback.say(clean)
            finally:
                self._on_end()
