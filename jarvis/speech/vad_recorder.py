"""Gravador VAD com Isolamento Estrito de Voz Humana (Passa-Banda 85-3400Hz + Silero/Neural VAD)."""

from __future__ import annotations

import audioop
from collections import deque
import logging
import math
import sys
import time
from typing import Callable

import numpy as np
import speech_recognition as sr

from jarvis.speech.audio_stream import apply_bandpass_85_3400, compute_rms

logger = logging.getLogger(__name__)

ECHO_GUARD_SECONDS = 0.65
MIN_HUMAN_SPEECH_MS = 300.0
DEFAULT_SPEECH_PROB_THRESHOLD = 0.75


class HumanVoiceFilter:
    """Filtra barulhos de animais (latidos, miados), batidas na mesa e ruídos externos (speech_prob >= 0.75)."""

    def __init__(self, sample_rate: int = 16000, speech_threshold: float = DEFAULT_SPEECH_PROB_THRESHOLD) -> None:
        self.sample_rate = sample_rate
        self.speech_threshold = speech_threshold
        self.model: object | None = None
        self._init_neural_vad()

    def _init_neural_vad(self) -> None:
        try:
            import torch  # type: ignore[import-not-found]
            self.model, _ = torch.hub.load("snakers4/silero-vad", "silero_vad", force_reload=False, onnx=False)
            self.model.eval()  # type: ignore[attr-defined]
        except Exception:
            self.model = None

    def compute_speech_prob(self, audio_chunk: np.ndarray | bytes, sample_rate: int | None = None) -> float:
        sr_rate = sample_rate or self.sample_rate
        arr = np.frombuffer(audio_chunk, dtype=np.int16) if isinstance(audio_chunk, bytes) else audio_chunk
        if len(arr) < 64:
            return 0.0
        audio_f32 = arr.astype(np.float32) / 32768.0
        fft_spec = np.abs(np.fft.rfft(audio_f32))
        freqs = np.fft.rfftfreq(len(audio_f32), d=1.0 / float(max(sr_rate, 8000)))
        total_energy = float(np.sum(fft_spec)) + 1e-8
        vocal_ratio = float(np.sum(fft_spec[(freqs >= 85.0) & (freqs <= 3400.0)])) / total_energy
        if vocal_ratio < 0.55:
            return round(vocal_ratio * 0.5, 3)

        if self.model is not None and len(audio_f32) >= 512:
            try:
                import torch  # type: ignore[import-not-found]
                with torch.no_grad():
                    return float(self.model(torch.from_numpy(audio_f32[:512]), sr_rate).item())  # type: ignore[misc]
            except Exception:
                pass

        formant_ratio = float(np.sum(fft_spec[(freqs >= 250.0) & (freqs <= 2800.0)])) / total_energy
        crest = float(np.max(np.abs(audio_f32))) / (float(np.sqrt(np.mean(audio_f32 * audio_f32))) + 1e-6)
        penalty = 0.25 if crest > 7.5 else 0.0
        return round(max(0.0, min(0.99, (vocal_ratio * 0.55) + (formant_ratio * 0.55) - penalty)), 3)

    def is_human_speech(self, audio_chunk_int16: np.ndarray | bytes, sample_rate: int | None = None) -> bool:
        return self.compute_speech_prob(audio_chunk_int16, sample_rate=sample_rate) >= self.speech_threshold


class AdaptiveVadRecorder:
    """Detecta fala humana real (speech_prob >= 0.75 por >= 300ms) e ignora ruídos/animais."""

    def __init__(self, on_volume: Callable[..., None] | None = None, silence_duration: float = 2.2) -> None:
        self._on_volume = on_volume
        self._noise_floor: float | None = None
        self._sensitivity: float = 2.5
        self.silence_duration = float(silence_duration)
        self.pause_threshold = float(silence_duration)
        self._voice_filter = HumanVoiceFilter(speech_threshold=DEFAULT_SPEECH_PROB_THRESHOLD)
        self._last_ui_time = 0.0
        self._echo_guard_until = 0.0

    def set_sensitivity(self, value: float) -> None:
        self._sensitivity = max(1.0, min(6.0, float(value)))

    def set_silence_duration(self, seconds: float) -> None:
        self.silence_duration = max(0.5, min(5.0, float(seconds)))
        self.pause_threshold = self.silence_duration

    def record_phrase(
        self, stream: object, sample_rate: int, sample_width: int, chunk_size: int,
        is_speaking: Callable[[], bool] | None = None, stop_event: object | None = None,
        reopen_event: object | None = None, terminal: object | None = None,
    ) -> tuple[sr.AudioData | None, str | None, float, int]:
        sec_per_chunk = float(chunk_size) / float(max(sample_rate, 8000))
        short_pause = max(5, int(0.58 / sec_per_chunk))
        breath_pause = max(short_pause, int(self.silence_duration / sec_per_chunk))
        min_human_chunks = max(3, int((MIN_HUMAN_SPEECH_MS / 1000.0) / sec_per_chunk))
        max_phrase_chunks = max(30, int(9.0 / sec_per_chunk))
        pre_roll: deque[bytes] = deque(maxlen=max(4, int(0.24 / sec_per_chunk)))
        recorded: list[bytes] = []
        speaking_started, human_chunks, silence_chunks, zero_chunks, peak_rms = False, 0, 0, 0, 0

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

            raw_buf = self._read_chunk(stream, chunk_size)
            if not raw_buf:
                time.sleep(0.02)
                continue
            buf = apply_bandpass_85_3400(raw_buf, sample_rate=sample_rate)
            raw_rms = compute_rms(buf)
            zero_chunks = zero_chunks + 1 if raw_rms == 0 else 0
            if zero_chunks >= 35:
                return None, None, -2.0, 0

            rms = int(raw_rms * (self._sensitivity / 2.0))
            if self._noise_floor is None:
                self._noise_floor = float(max(4, min(rms, 350)))
            start_threshold = max(int(self._noise_floor * 1.32) + 10, 16)

            if is_speaking and is_speaking():
                self._echo_guard_until = time.monotonic() + ECHO_GUARD_SECONDS
            if time.monotonic() < self._echo_guard_until:
                self._update_hud(rms, int(self._noise_floor), start_threshold, is_voice=False)
                recorded.clear()
                pre_roll.clear()
                speaking_started, human_chunks, silence_chunks = False, 0, 0
                continue

            prob = self._voice_filter.compute_speech_prob(buf, sample_rate=sample_rate) if rms >= start_threshold else 0.0
            is_human = rms >= start_threshold and prob >= DEFAULT_SPEECH_PROB_THRESHOLD

            if not speaking_started:
                self._noise_floor = (
                    self._noise_floor * 0.85 + rms * 0.15 if rms <= self._noise_floor
                    else min(400.0, self._noise_floor * 0.97 + rms * 0.03) if not is_human else self._noise_floor
                )
                pre_roll.append(buf)
                self._update_hud(rms, int(self._noise_floor), start_threshold, is_voice=False)
                if is_human:
                    speaking_started, human_chunks, silence_chunks, peak_rms = True, 1, 0, rms
                    recorded.extend(pre_roll)
            else:
                recorded.append(buf)
                peak_rms = max(peak_rms, rms)
                cont_thresh = max(start_threshold, int(self._noise_floor + (peak_rms - self._noise_floor) * 0.18))
                if rms >= cont_thresh and prob >= 0.68:
                    human_chunks += 1
                    silence_chunks = max(0, silence_chunks - 2)
                else:
                    silence_chunks += 1

                self._update_hud(rms, int(self._noise_floor), cont_thresh, is_voice=True)
                pause_needed = breath_pause if (human_chunks * sec_per_chunk) >= 0.85 else short_pause
                if silence_chunks >= pause_needed or len(recorded) >= max_phrase_chunks:
                    if human_chunks >= min_human_chunks:
                        raw_pcm = b"".join(recorded)
                        if 0 < peak_rms < 1100:
                            gain = min(7.0, (1400.0 / float(peak_rms)) * (self._sensitivity / 2.5))
                            try:
                                raw_pcm = audioop.mul(raw_pcm, sample_width, gain)
                            except Exception:
                                pass
                        return sr.AudioData(raw_pcm, sample_rate, sample_width), None, len(recorded) * sec_per_chunk, peak_rms
                    recorded.clear()
                    speaking_started, human_chunks, silence_chunks = False, 0, 0

    @staticmethod
    def _read_chunk(stream: object, size: int) -> bytes:
        try:
            return getattr(stream, "read")(size, exception_on_overflow=False)  # type: ignore[no-any-return]
        except Exception:
            return b""

    def _update_hud(self, rms: int, noise: int, threshold: int, is_voice: bool) -> None:
        level = (
            min(1.0, max(0.32, math.sqrt(max(0.0, float(rms - noise)) / max(float(threshold * 1.4), 25.0)) * 0.68))
            if is_voice else min(0.20, max(0.06 if rms > 0 else 0.0, (float(rms) / max(float(threshold * 1.3), 20.0)) * 0.22))
        )
        if self._on_volume:
            try:
                self._on_volume(level, rms, noise, threshold, is_voice)
            except TypeError:
                self._on_volume(level)
        now = time.time()
        if now - self._last_ui_time >= (0.05 if is_voice else 0.22):
            self._last_ui_time = now
            bars = max(1 if rms > 0 else 0, int(level * 18))
            tag = "🟢 [VOZ HUMANA!]" if is_voice else "🎙️ [ESCUTA ATIVA]"
            sys.stdout.write(f"\r{tag} [{'█' * bars + '░' * (18 - bars)}] Nível:{int(level * 100):3d}% | Voz:{rms:4d} RMS ")
            sys.stdout.flush()
