"""Dispositivos de áudio do sistema, medidor de RMS e adaptador de fluxo 16000Hz."""

from __future__ import annotations

import logging
import math
import os
import queue
import struct
import threading
import time
from dataclasses import dataclass
from typing import Callable

import pyaudio

logger = logging.getLogger(__name__)

CHUNK_SIZE = 1024
SAMPLE_RATE = 16000
FORMAT = pyaudio.paInt16
CHANNELS = 1


@dataclass(frozen=True)
class AudioDeviceInfo:
    """Informações de um dispositivo de entrada de microfone."""

    index: int
    name: str
    sample_rate: int
    channels: int


def compute_rms(data: bytes) -> int:
    """Calcula o valor RMS (Root Mean Square) da energia sonora do buffer PCM 16-bit."""
    count = len(data) // 2
    if count == 0:
        return 0
    try:
        import audioop
        return audioop.rms(data, 2)
    except ImportError:
        shorts = struct.unpack(f"<{count}h", data)
        return int(math.sqrt(sum(s * s for s in shorts) / count))


def apply_bandpass_85_3400(data: bytes, sample_rate: int = SAMPLE_RATE) -> bytes:
    """Filtro Passa-Banda (85Hz a 3400Hz) para cortar latidos/miados agudos e batidas graves."""
    if len(data) < 64:
        return data
    try:
        import numpy as np
        samples = np.frombuffer(data, dtype=np.int16).astype(np.float32)
        spec = np.fft.rfft(samples)
        freqs = np.fft.rfftfreq(len(samples), d=1.0 / float(max(sample_rate, 8000)))
        filtered = np.fft.irfft(spec * ((freqs >= 85.0) & (freqs <= 3400.0)), n=len(samples))
        return np.clip(filtered, -32768.0, 32767.0).astype(np.int16).tobytes()
    except Exception:
        return data


def list_input_devices() -> list[AudioDeviceInfo]:
    """Varre todos os dispositivos físicos e lógicos com canais de gravação disponíveis."""
    p = pyaudio.PyAudio()
    devices: list[AudioDeviceInfo] = []
    try:
        count = p.get_device_count()
        for idx in range(count):
            try:
                info = p.get_device_info_by_index(idx)
                max_in = int(info.get("maxInputChannels", 0))
                if max_in > 0:
                    name = str(info.get("name", f"Microfone {idx}"))
                    rate = int(info.get("defaultSampleRate", 48000))
                    devices.append(AudioDeviceInfo(index=idx, name=name, sample_rate=rate, channels=max_in))
            except Exception:
                continue
    finally:
        p.terminate()
    return devices


def test_device_connectivity(device_index: int) -> bool:
    """Verifica se a porta do microfone abre e responde com fluxo ativo sem erro."""
    p = pyaudio.PyAudio()
    try:
        info = p.get_device_info_by_index(device_index)
        rate = int(info.get("defaultSampleRate", SAMPLE_RATE))
        stream = p.open(
            format=FORMAT,
            channels=1,
            rate=rate,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=256,
        )
        data = stream.read(256, exception_on_overflow=False)
        stream.stop_stream()
        stream.close()
        return len(data) > 0
    except Exception:
        return False
    finally:
        p.terminate()


def pick_default_device_index(devices: list[AudioDeviceInfo]) -> int | None:
    """Seleciona o microfone físico ativo com conectividade comprovada na porta."""
    if not devices:
        return None

    env_idx = os.getenv("JARVIS_MIC_INDEX") or os.getenv("JARVIS_MICROPHONE_INDEX")
    if env_idx and env_idx.strip().isdigit():
        target = int(env_idx.strip())
        for d in devices:
            if d.index == target:
                return d.index

    blacklist = ("mixagem", "stereo mix", "virtual", "cable", "steam", "mapeador")
    priority = ("microfone", "microphone", "mic", "headset", "realtek", "array", "fone", "usb")

    # 1. Filtra dispositivos físicos prioritários com conectividade real confirmada
    for d in devices:
        low = d.name.lower()
        if any(b in low for b in blacklist):
            continue
        if any(p in low for p in priority) and test_device_connectivity(d.index):
            return d.index

    # 2. Testa o dispositivo padrão do Windows
    try:
        p = pyaudio.PyAudio()
        try:
            def_info = p.get_default_input_device_info()
            def_idx = int(def_info.get("index", -1))
            if any(d.index == def_idx for d in devices) and test_device_connectivity(def_idx):
                return def_idx
        finally:
            p.terminate()
    except Exception:
        pass

    # 3. Qualquer dispositivo conectado que responda ao teste de porta
    for d in devices:
        if test_device_connectivity(d.index):
            return d.index

    return devices[0].index


class ContinuousAudioStream:
    """Adaptador de fluxo contínuo de áudio para compatibilidade e monitoramento."""

    def __init__(
        self,
        device_index: int | None = None,
        on_volume: Callable[[float], None] | None = None,
    ) -> None:
        self._device_index = device_index
        self._on_volume = on_volume
        self._queue: queue.Queue[tuple[bytes, int]] = queue.Queue(maxsize=60)
        self._stop_event = threading.Event()

    @property
    def sample_rate(self) -> int:
        return SAMPLE_RATE

    @property
    def device_index(self) -> int | None:
        return self._device_index

    def start(self, device_index: int | None = None) -> bool:
        if device_index is not None:
            self._device_index = device_index
        self._stop_event.clear()
        return True

    def read_chunk(self, timeout: float = 0.1) -> tuple[bytes, int]:
        try:
            return self._queue.get(timeout=timeout)
        except queue.Empty:
            return b"", 0

    def put_chunk(self, data: bytes, rms: int) -> None:
        if not self._queue.full():
            self._queue.put_nowait((data, rms))
        if self._on_volume:
            self._on_volume(min(rms / 800.0, 1.0))

    def stop(self) -> None:
        self._stop_event.set()
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except Exception:
                break
