"""Stream wrapper com Ganho Automático (AGC) e telemetria acústica ao vivo no CMD."""

from __future__ import annotations

import audioop
import sys
import time
from typing import Callable

from jarvis.speech.audio_stream import compute_rms


class MeteredAudioStream:
    """Amplifica voz baixa automaticamente (AGC) e exibe VU meter em tempo real no CMD."""

    def __init__(self, raw_stream: object, on_volume: Callable[[float], None] | None = None) -> None:
        self._raw = raw_stream
        self._on_volume = on_volume
        self._last_update = 0.0
        self._noise_floor = 4.0

    def read(self, size: int, exception_on_overflow: bool = False) -> bytes:
        try:
            data = getattr(self._raw, "read")(size, exception_on_overflow=exception_on_overflow)
        except TypeError:
            try:
                data = getattr(self._raw, "read")(size)
            except Exception:
                data = b""
        except Exception:
            data = b""

        if not data:
            return b""

        raw_rms = compute_rms(data)
        if raw_rms < self._noise_floor:
            self._noise_floor = max(1.0, self._noise_floor * 0.95 + raw_rms * 0.05)
        else:
            self._noise_floor = min(25.0, self._noise_floor * 0.995 + raw_rms * 0.005)

        is_voice = raw_rms > max(6, int(self._noise_floor * 1.6))

        # Ganho Automático (AGC): amplifica microfones baixos para nitidez máxima na transcrição
        if is_voice and 0 < raw_rms < 1400:
            gain = min(16.0, max(1.5, 1200.0 / float(raw_rms)))
            try:
                data = audioop.mul(data, 2, gain)
            except Exception:
                pass

        level = min(raw_rms / 180.0, 1.0) if is_voice else min(raw_rms / 300.0, 0.12)
        if self._on_volume:
            self._on_volume(level)

        now = time.time()
        interval = 0.05 if is_voice else 0.45
        if now - self._last_update >= interval:
            self._last_update = now
            bars = max(1 if is_voice else 0, int(level * 20))
            meter_str = "█" * bars + "░" * (20 - bars)
            pct = int(level * 100)
            if is_voice:
                sys.stdout.write(
                    f"\r🟢 [OUVINDO SUA VOZ!] Sinal: [{meter_str}] {pct}% (RMS:{raw_rms}) | CAPTANDO FALA...      "
                )
            else:
                sys.stdout.write(
                    f"\r🎙️ [MICROFONE ATIVO] Sinal: [{meter_str}] {pct}% (RMS:{raw_rms}) | Pode falar seu comando... "
                )
            sys.stdout.flush()

        return data  # type: ignore[no-any-return]

    def close(self) -> None:
        try:
            getattr(self._raw, "close", lambda: None)()
        except Exception:
            pass

    def __getattr__(self, name: str) -> object:
        return getattr(self._raw, name)
