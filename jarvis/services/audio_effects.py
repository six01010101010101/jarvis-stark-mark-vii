"""Efeitos sonoros nativos de alta fidelidade Stark Industries (Reator Arc e Chimes)."""

from __future__ import annotations

import logging
import math
from pathlib import Path
import struct
import wave
import winsound

logger = logging.getLogger(__name__)

DEFAULT_SOUNDS_DIR = Path(__file__).resolve().parent.parent.parent / "jarvis_sounds"
SAMPLE_RATE = 44100


def _write_wav(path: Path, samples: list[float]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        raw_data = bytearray()
        for s in samples:
            clamped = max(-1.0, min(1.0, s))
            int_val = int(clamped * 32767.0)
            raw_data.extend(struct.pack("<h", int_val))
        wf.writeframes(raw_data)


def generate_sound_effects(target_dir: Path = DEFAULT_SOUNDS_DIR) -> None:
    """Gera arquivos WAV de áudio sintetizado para a interface Stark."""
    target_dir.mkdir(parents=True, exist_ok=True)

    # 1. Som de Boot do Reator Arc (400ms, swell harmônico)
    boot_path = target_dir / "stark_boot.wav"
    if not boot_path.exists():
        samples = []
        duration = 0.45
        total_samples = int(SAMPLE_RATE * duration)
        for i in range(total_samples):
            t = i / SAMPLE_RATE
            env = math.sin(math.pi * (i / total_samples)) ** 1.5
            freq = 300 + 400 * (t / duration)
            wave_val = 0.5 * math.sin(2 * math.pi * freq * t) + 0.3 * math.sin(4 * math.pi * freq * t)
            samples.append(wave_val * env * 0.7)
        _write_wav(boot_path, samples)

    # 2. Som de Ativação do Jarvis (Chirp holográfico de 90ms)
    wake_path = target_dir / "stark_wake.wav"
    if not wake_path.exists():
        samples = []
        duration = 0.10
        total_samples = int(SAMPLE_RATE * duration)
        for i in range(total_samples):
            t = i / SAMPLE_RATE
            env = math.exp(-25.0 * t)
            freq = 1200 + 1600 * (t / duration)
            wave_val = math.sin(2 * math.pi * freq * t)
            samples.append(wave_val * env * 0.6)
        _write_wav(wake_path, samples)

    # 3. Ping de Confirmação (120ms)
    ping_path = target_dir / "stark_ping.wav"
    if not ping_path.exists():
        samples = []
        duration = 0.12
        total_samples = int(SAMPLE_RATE * duration)
        for i in range(total_samples):
            t = i / SAMPLE_RATE
            env = math.exp(-30.0 * t)
            wave_val = math.sin(2 * math.pi * 1046.5 * t)
            samples.append(wave_val * env * 0.5)
        _write_wav(ping_path, samples)


class StarkSoundPlayer:
    """Reprodutor de efeitos sonoros assíncronos do Jarvis."""

    def __init__(self, sounds_dir: Path = DEFAULT_SOUNDS_DIR, enabled: bool = True) -> None:
        self._dir = sounds_dir
        self._enabled = enabled
        if self._enabled:
            generate_sound_effects(self._dir)

    def _play(self, filename: str) -> None:
        if not self._enabled:
            return
        path = self._dir / filename
        if path.exists():
            try:
                winsound.PlaySound(str(path), winsound.SND_FILENAME | winsound.SND_ASYNC)
            except Exception as exc:  # noqa: BLE001
                logger.debug("Falha ao tocar som %s: %s", filename, exc)

    def play_boot(self) -> None:
        self._play("stark_boot.wav")

    def play_wake(self) -> None:
        self._play("stark_wake.wav")

    def play_ping(self) -> None:
        self._play("stark_ping.wav")
