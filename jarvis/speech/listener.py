"""Motor de escuta contínua 24/7 em thread dedicada com VAD Adaptativo e log no CMD."""

from __future__ import annotations

import logging
import queue
import threading
import time
from typing import Callable

import speech_recognition as sr

from jarvis.speech.audio_stream import list_input_devices, pick_default_device_index
from jarvis.speech.transcriber import MultiEngineTranscriber
from jarvis.speech.vad_recorder import AdaptiveVadRecorder

logger = logging.getLogger(__name__)


class MicrophoneError(Exception):
    """Nenhum microfone disponível ou falha ao acessá-lo."""


class GoogleSpeechListener:
    """Escuta contínua em thread dedicada mantendo o medidor de nível/sensibilidade 100% ativo."""

    def __init__(
        self,
        language: str = "pt-BR",
        device_index: int | None = None,
        timeout_seconds: float | None = None,
        is_speaking: Callable[[], bool] | None = None,
        on_volume: Callable[..., None] | None = None,
        on_status: Callable[[str], None] | None = None,
        terminal: object | None = None,
        gemini: object | None = None,
    ) -> None:
        self._language, self._timeout = language, timeout_seconds
        self._is_speaking, self._on_volume = is_speaking, on_volume
        self._on_status, self._terminal, self._gemini = on_status, terminal, gemini
        self._stop_event = threading.Event()
        self._reopen_event = threading.Event()
        self._lock = threading.Lock()
        self._vpn_mode = False
        self._switched_default = False
        self._phrase_queue: queue.Queue[tuple[sr.AudioData | None, str | None, float, int]] = queue.Queue()

        self._recognizer = sr.Recognizer()
        self._transcriber = MultiEngineTranscriber(self._recognizer, language=language, gemini=gemini)
        self._vad = AdaptiveVadRecorder(on_volume=on_volume)

        self._device_index = device_index
        self._mic: sr.Microphone | None = None
        self.device_name, self.sample_rate = "Microfone Padrão", 16000
        self._init_microphone()
        self._worker = threading.Thread(target=self._capture_loop, name="jarvis-mic-capture", daemon=True)
        self._worker.start()

    def _init_microphone(self) -> None:
        devs = list_input_devices()
        target = self._device_index if self._device_index is not None else pick_default_device_index(devs)
        self._device_index = target
        for d in devs:
            if d.index == target:
                self.device_name, self.sample_rate = d.name, d.sample_rate
                break
        try:
            self._mic = sr.Microphone(device_index=self._device_index)
            logger.info("🎙️ [LISTENER] Porta ativa [%s] (%s)", self._device_index, self.device_name)
        except Exception as exc:
            logger.warning("🎙️ [LISTENER] Falha na porta [%s] (%s), usando padrão.", self._device_index, exc)
            try:
                self._mic = sr.Microphone(device_index=None)
            except Exception:
                self._mic = None

    def set_device(self, device_index: int) -> bool:
        """Altera o microfone ativo em tempo real."""
        with self._lock:
            self._device_index = device_index
            self._switched_default = False
            self._init_microphone()
            self._reopen_event.set()
            return self._mic is not None

    def set_sensitivity(self, value: float) -> None:
        """Altera a sensibilidade do microfone em tempo real."""
        self._vad.set_sensitivity(value)

    def _capture_loop(self) -> None:
        """Thread dedicada que lê o microfone sem pausas e atualiza o medidor VU em tempo real."""
        while not self._stop_event.is_set():
            if self._mic is None:
                self._init_microphone()
                if self._mic is None:
                    time.sleep(0.3)
                    continue

            with self._lock:
                mic = self._mic

            try:
                with mic as source:
                    if source.stream is None:
                        self._mic = sr.Microphone(device_index=None)
                        time.sleep(0.2)
                        continue

                    s_rate = int(getattr(source, "SAMPLE_RATE", 16000) or 16000)
                    s_width = int(getattr(source, "SAMPLE_WIDTH", 2) or 2)
                    c_size = int(getattr(source, "CHUNK", 1024) or 1024)

                    while not self._stop_event.is_set():
                        audio, typed, dur, peak_rms = self._vad.record_phrase(
                            stream=source.stream,
                            sample_rate=s_rate,
                            sample_width=s_width,
                            chunk_size=c_size,
                            is_speaking=self._is_speaking,
                            stop_event=self._stop_event,
                            reopen_event=self._reopen_event,
                            terminal=self._terminal,
                        )
                        if dur == -1.0:
                            break
                        if dur == -2.0 and not self._switched_default:
                            self._switched_default = True
                            self._mic = sr.Microphone(device_index=None)
                            break
                        if typed or audio is not None:
                            self._phrase_queue.put((audio, typed, dur, peak_rms))
            except Exception as exc:
                logger.debug("Reabrindo fluxo de microfone: %s", exc)
                time.sleep(0.2)

    def listen(self, idle_timeout: float = 1.0) -> str | None:
        """Consome frases da thread de captura; retorna None após `idle_timeout` s sem fala."""
        deadline = time.monotonic() + idle_timeout
        while not self._stop_event.is_set() and time.monotonic() < deadline:
            try:
                audio, typed, dur, peak_rms = self._phrase_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            if typed:
                print("\n==========================================================================", flush=True)
                print(f"📋 [LOG CMD 1/4 - ENTRADA CAPTADA] Digitado no CMD: \"{typed}\"", flush=True)
                print(f"📋 [LOG CMD 2/4 - LEITURA DA SUA FALA] Você disse: \"{typed}\" (Motor: Teclado-CMD)", flush=True)
                return typed

            if audio is None:
                continue

            print("\n==========================================================================", flush=True)
            print(
                f"📋 [LOG CMD 1/4 - VOZ CAPTADA] Microfone detectou sua fala "
                f"({dur:.1f}s | Pico Acústico: {peak_rms} RMS)",
                flush=True,
            )
            if self._on_status:
                self._on_status("🧠 Processando sua voz...")

            text, engine = self._transcriber.transcribe(audio)
            if text:
                self._dispatch_success(text, engine=engine)
                return text

            print("📋 [LOG CMD] ⚠️ Som sem fala nítida ignorado. Aguardando comando...", flush=True)
            if self._on_status:
                self._on_status("🟢 Ouvindo // Pode falar...")
        return None

    def _dispatch_success(self, text: str, engine: str) -> None:
        print(f"📋 [LOG CMD 2/4 - LEITURA DA SUA FALA] Você falou: \"{text}\" (Motor: {engine})", flush=True)
        logger.info("🎙️ [STT] %s transcreveu: '%s'", engine, text)
        if self._on_status:
            self._on_status(f"Você disse: '{text}'")

    def close(self) -> None:
        """Encerra o ouvinte."""
        self._stop_event.set()
