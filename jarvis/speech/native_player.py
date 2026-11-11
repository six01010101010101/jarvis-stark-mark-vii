"""Reprodução nativa de áudio MP3 no Windows com suporte a interrupção instantânea."""

from __future__ import annotations

import ctypes
import ctypes.wintypes
import logging
from pathlib import Path
import threading
import time

logger = logging.getLogger(__name__)


def pump_win32_messages() -> None:
    """Processa mensagens da fila do Windows para evitar congelamento de COM."""
    try:
        user32, msg = ctypes.windll.user32, ctypes.wintypes.MSG()
        while user32.PeekMessageW(ctypes.byref(msg), 0, 0, 0, 1):
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
    except Exception:
        pass


def play_mp3_native(mp3_path: Path, max_wait: float = 16.0, stop_event: threading.Event | None = None) -> bool:
    """Reproduz MP3 com aceleração 1.14x e cancelamento imediato quando stop_event é acionado."""
    if not mp3_path.exists() or mp3_path.stat().st_size == 0 or (stop_event and stop_event.is_set()):
        return False
    est_duration = max(0.55, min((mp3_path.stat().st_size / 6600.0) + 0.25, max_wait))
    try:
        import comtypes
        import comtypes.client
        comtypes.CoInitialize()
        wmp = comtypes.client.CreateObject("WMPlayer.OCX")
        wmp.settings.volume = 100
        wmp.settings.rate = 1.14
        media = wmp.newMedia(str(mp3_path.resolve()))
        wmp.currentMedia = media
        wmp.controls.play()
        t_start = time.time()
        while time.time() - t_start < 1.2:
            pump_win32_messages()
            if stop_event and stop_event.is_set():
                wmp.controls.stop()
                wmp.close()
                return True
            if wmp.playState == 3:
                break
            time.sleep(0.015)
        if wmp.playState == 3:
            t0 = time.time()
            while time.time() - t0 < est_duration:
                if stop_event and stop_event.is_set():
                    break
                pump_win32_messages()
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
        alias = f"jarvis_mci_{int(time.time() * 1000)}"
        winmm = ctypes.windll.winmm
        if winmm.mciSendStringW(f'open "{buf.value or str(mp3_path)}" type mpegvideo alias {alias}', None, 0, 0) == 0:
            winmm.mciSendStringW(f"play {alias}", None, 0, 0)
            t0 = time.time()
            while time.time() - t0 < est_duration + 0.3:
                if stop_event and stop_event.is_set():
                    break
                pump_win32_messages()
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
