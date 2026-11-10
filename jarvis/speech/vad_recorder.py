"""Gravador com Detecção de Atividade de Voz (VAD) adaptativa, sensibilidade e medidor VU."""

from __future__ import annotations

import audioop
from collections import deque
import math
import sys
import time
from typing import Callable

import speech_recognition as sr

from jarvis.speech.audio_stream import compute_rms

ECHO_GUARD_SECONDS = 0.65


class AdaptiveVadRecorder:
    """Detecta início e fim da fala e atualiza o nível e sensibilidade em tempo real."""

    def __init__(self, on_volume: Callable[..., None] | None = None) -> None:
        self._on_volume = on_volume
        self._noise_floor: float | None = None
        self._sensitivity: float = 2.5
        self._last_ui_time = 0.0
        self._echo_guard_until = 0.0

    def set_sensitivity(self, value: float) -> None:
        """Define o multiplicador de sensibilidade do microfone (1.0x a 6.0x)."""
        self._sensitivity = max(1.0, min(6.0, float(value)))

    def record_phrase(
        self,
        stream: object,
        sample_rate: int,
        sample_width: int,
        chunk_size: int,
        is_speaking: Callable[[], bool] | None = None,
        stop_event: object | None = None,
        reopen_event: object | None = None,
        terminal: object | None = None,
    ) -> tuple[sr.AudioData | None, str | None, float, int]:
        """Escuta o fluxo até captar uma frase completa mantendo o medidor de áudio vivo."""
        sec_per_chunk = float(chunk_size) / float(max(sample_rate, 8000))
        pause_chunks_needed = max(4, int(0.45 / sec_per_chunk))
        min_voice_chunks = max(2, int(0.14 / sec_per_chunk))
        max_phrase_chunks = max(22, int(4.2 / sec_per_chunk))

        pre_roll: deque[bytes] = deque(maxlen=max(4, int(0.24 / sec_per_chunk)))
        recorded: list[bytes] = []
        speaking_started = False
        voice_chunks = 0
        silence_chunks = 0
        zero_chunks = 0
        peak_rms = 0

        while True:
            if stop_event and getattr(stop_event, "is_set", lambda: False)():
                return None, None, 0.0, 0
            if reopen_event and getattr(reopen_event, "is_set", lambda: False)():
                getattr(reopen_event, "clear", lambda: None)()
                return None, None, -1.0, 0

            if not speaking_started and terminal and hasattr(terminal, "get_input"):
                typed = terminal.get_input(timeout=0.005)
                if typed:
                    return None, str(typed), 0.0, 0

            buf = self._read_chunk(stream, chunk_size)
            if not buf:
                time.sleep(0.02)
                continue

            raw_rms = compute_rms(buf)
            if raw_rms == 0:
                zero_chunks += 1
                if zero_chunks >= 35:
                    return None, None, -2.0, 0
            else:
                zero_chunks = 0
            rms = int(raw_rms * (self._sensitivity / 2.0))
            if self._noise_floor is None:
                self._noise_floor = float(max(4, min(rms, 350)))

            start_threshold = max(int(self._noise_floor * 1.32) + 10, 16)

            # Enquanto o Jarvis fala (e por um breve eco depois), drena o áudio sem gravar a própria voz
            if is_speaking and is_speaking():
                self._echo_guard_until = time.monotonic() + ECHO_GUARD_SECONDS
            if time.monotonic() < self._echo_guard_until:
                self._update_hud(rms, int(self._noise_floor), start_threshold, is_voice=False)
                recorded.clear()
                pre_roll.clear()
                speaking_started = False
                voice_chunks = 0
                silence_chunks = 0
                continue

            if not speaking_started:
                is_voice = rms >= start_threshold
                if rms <= self._noise_floor:
                    self._noise_floor = self._noise_floor * 0.85 + rms * 0.15
                elif not is_voice:
                    self._noise_floor = min(400.0, self._noise_floor * 0.97 + rms * 0.03)

                pre_roll.append(buf)
                self._update_hud(rms, int(self._noise_floor), start_threshold, is_voice=False)

                if is_voice:
                    speaking_started = True
                    voice_chunks = 1
                    silence_chunks = 0
                    peak_rms = rms
                    recorded.extend(pre_roll)
            else:
                recorded.append(buf)
                if rms > peak_rms:
                    peak_rms = rms

                continue_threshold = max(
                    start_threshold,
                    int(self._noise_floor + (peak_rms - self._noise_floor) * 0.18),
                )
                is_voice = rms >= continue_threshold

                if is_voice:
                    voice_chunks += 1
                    silence_chunks = max(0, silence_chunks - 2)
                else:
                    silence_chunks += 1

                self._update_hud(rms, int(self._noise_floor), continue_threshold, is_voice=True)

                if silence_chunks >= pause_chunks_needed or len(recorded) >= max_phrase_chunks:
                    if voice_chunks >= min_voice_chunks:
                        raw_pcm = b"".join(recorded)
                        if 0 < peak_rms < 1100:
                            gain = min(7.0, (1400.0 / float(peak_rms)) * (self._sensitivity / 2.5))
                            try:
                                raw_pcm = audioop.mul(raw_pcm, sample_width, gain)
                            except Exception:
                                pass
                        dur = len(recorded) * sec_per_chunk
                        return sr.AudioData(raw_pcm, sample_rate, sample_width), None, dur, peak_rms

                    recorded.clear()
                    speaking_started = False
                    voice_chunks = 0
                    silence_chunks = 0

    @staticmethod
    def _read_chunk(stream: object, size: int) -> bytes:
        try:
            return getattr(stream, "read")(size, exception_on_overflow=False)  # type: ignore[no-any-return]
        except TypeError:
            try:
                return getattr(stream, "read")(size)  # type: ignore[no-any-return]
            except Exception:
                return b""
        except Exception:
            return b""

    def _update_hud(self, rms: int, noise: int, threshold: int, is_voice: bool) -> None:
        if is_voice:
            ratio = max(0.0, float(rms - noise)) / max(float(threshold * 1.4), 25.0)
            level = min(1.0, max(0.32, math.sqrt(ratio) * 0.68))
        else:
            base = float(rms) / max(float(threshold * 1.3), 20.0)
            level = min(0.20, max(0.06 if rms > 0 else 0.0, base * 0.22))

        if self._on_volume:
            try:
                self._on_volume(level, rms, noise, threshold, is_voice)
            except TypeError:
                self._on_volume(level)

        now = time.time()
        interval = 0.05 if is_voice else 0.22
        if now - self._last_ui_time >= interval:
            self._last_ui_time = now
            bars = max(1 if rms > 0 else 0, int(level * 18))
            meter = "█" * bars + "░" * (18 - bars)
            pct = int(level * 100)
            if is_voice:
                sys.stdout.write(
                    f"\r🟢 [CAPTANDO VOZ!] [{meter}] Nível:{pct:3d}% | Voz:{rms:4d} RMS | Sens:{self._sensitivity:.1f}x (Limiar:{threshold:3d}) "
                )
            else:
                sys.stdout.write(
                    f"\r🎙️ [ESCUTA ATIVA] [{meter}] Nível:{pct:3d}% | Voz:{rms:4d} RMS | Sens:{self._sensitivity:.1f}x (Limiar:{threshold:3d}) "
                )
            sys.stdout.flush()
