"""Ponte de console e terminal para transcrição de áudio e interação bidirecional do J.A.R.V.I.S."""

from __future__ import annotations

import logging
import queue
import sys
import threading
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class TerminalBridge:
    """Gerencia a visibilidade no CMD e a entrada paralela por teclado no terminal."""

    def __init__(self, enabled: bool = True) -> None:
        self._enabled = enabled
        self._queue: queue.Queue[str] = queue.Queue()
        self._stop_event = threading.Event()
        self._reader_thread: threading.Thread | None = None
        if self._enabled:
            self._enable_ansi_colors()
            self._start_reader()

    @staticmethod
    def _enable_ansi_colors() -> None:
        """Ativa cores ANSI (sinal verde) no console do Windows (ENABLE_VIRTUAL_TERMINAL_PROCESSING)."""
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetStdHandle(-11)
            mode = ctypes.c_uint32()
            if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                kernel32.SetConsoleMode(handle, mode.value | 0x0004)
        except (AttributeError, OSError) as exc:
            logger.debug("Cores ANSI indisponíveis neste console: %s", exc)

    def _start_reader(self) -> None:
        self._reader_thread = threading.Thread(
            target=self._read_stdin_loop,
            name="jarvis-terminal-reader",
            daemon=True,
        )
        self._reader_thread.start()

    def _read_stdin_loop(self) -> None:
        """Lê comandos digitados pelo usuário diretamente na janela do CMD/terminal."""
        while not self._stop_event.is_set():
            try:
                line = sys.stdin.readline()
                if not line:
                    time.sleep(0.1)
                    continue
                clean = line.strip()
                if clean:
                    print(f"\n[CMD-TECLADO] ⌨️ Entrada do terminal capturada: \"{clean}\"", flush=True)
                    self._queue.put(clean)
            except Exception:
                time.sleep(0.3)

    def print_hud_banner(self, mic_name: str, sample_rate: int, dev_idx: int | None = None) -> None:
        """Exibe o cabeçalho de prontidão acústica e conectividade da porta no terminal CMD."""
        if not self._enabled:
            return
        idx_str = f"Porta #{dev_idx} - " if dev_idx is not None else ""
        banner = (
            "\n"
            + "=" * 74
            + "\n"
            + " 🔌 [CONECTIVIDADE DA PORTA] SENSOR ACÚSTICO ONLINE E CONECTADO\n"
            + f" 📡 Porta Selecionada: {idx_str}{mic_name} ({sample_rate}Hz)\n"
            + " 🟢 Status: MICROFONE ATIVO // OUVINDO SUA VOZ EM TEMPO REAL\n"
            + " ⚡ Quando você falar, o sinal sonoro e a transcrição aparecerão aqui!\n"
            + "=" * 74
            + "\n"
        )
        print(banner, flush=True)

    def notify_listening(self) -> None:
        if self._enabled:
            print("\r[CMD-AUDIO] 🎙️ Ouvindo microfone... (Diga 'Jarvis' para ativar)...   ", end="", flush=True)

    def notify_capturing(self) -> None:
        if self._enabled:
            print("\n[CMD-AUDIO] ⚡ Áudio captado! Enviando para transcrição Google STT...", flush=True)

    def notify_transcription(self, text: str) -> None:
        if self._enabled:
            print(f"[CMD-AUDIO] 📝 TRANSCRIÇÃO OBTIDA: \"{text}\"", flush=True)

    def notify_wake(self, phrase: str) -> None:
        if self._enabled:
            print(f"[CMD-JARVIS] ⚡ Nome 'Jarvis' identificado na fala: \"{phrase}\"!", flush=True)

    def notify_reply(self, reply_text: str) -> None:
        if self._enabled:
            print(f"[CMD-JARVIS] 🤖 J.A.R.V.I.S.: \"{reply_text}\"", flush=True)

    def get_input(self, timeout: float = 0.05) -> str | None:
        """Retorna comando digitado no terminal, se houver."""
        try:
            return self._queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def close(self) -> None:
        self._stop_event.set()
