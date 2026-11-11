"""Motor de escuta contínua 24/7 em thread dedicada com VAD Adaptativo, Desempacotamento Seguro e Log CMD."""

from __future__ import annotations

import logging
import queue
import threading
import time
from typing import Callable

import speech_recognition as sr

from jarvis.speech.audio_stream import list_input_devices, pick_default_device_index
from jarvis.speech.metered_stream import MeteredAudioStream
from jarvis.speech.transcriber import MultiEngineTranscriber, unpack_transcription
from jarvis.speech.vad_recorder import AdaptiveVadRecorder

logger = logging.getLogger(__name__)

DEFAULT_ENERGY_THRESHOLD = 140
MIN_ENERGY_THRESHOLD = 45
MAX_ENERGY_THRESHOLD = 480


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
        on_language_detected: Callable[[str], None] | None = None,
        terminal: object | None = None,
        gemini: object | None = None,
    ) -> None:
        self._language, self._timeout = language, timeout_seconds
        self._is_speaking, self._on_volume = is_speaking, on_volume
        self._on_status, self._terminal, self._gemini = on_status, terminal, gemini
        self._on_language_detected = on_language_detected
        self._stop_event = threading.Event()
        self._reopen_event = threading.Event()
        self._lock = threading.Lock()
        self._switched_default = False
        self._phrase_queue: queue.Queue[tuple[sr.AudioData | None, str | None, float, int]] = queue.Queue()

        self._recognizer = sr.Recognizer()
        self._recognizer.energy_threshold = DEFAULT_ENERGY_THRESHOLD
        self._recognizer.dynamic_energy_threshold = True
        self._recognizer.pause_threshold = 0.65
        self._transcriber = MultiEngineTranscriber(self._recognizer, language=language, gemini=gemini)
        self._vad = AdaptiveVadRecorder(on_volume=on_volume)

        self._device_index = device_index
        self._mic: sr.Microphone | None = None
        self.device_name, self.sample_rate = "Microfone Padrão", 16000
        self._init_microphone()
        self._worker = threading.Thread(target=self._capture_loop, name="jarvis-mic-capture", daemon=True)

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
            except Exception as fallback_exc:
                logger.error("Falha ao abrir microfone padrão: %s", fallback_exc)
                self._mic = None

    def set_device(self, device_index: int) -> bool:
        with self._lock:
            self._device_index = device_index
            self._switched_default = False
            self._init_microphone()
            self._reopen_event.set()
            return self._mic is not None

    def set_sensitivity(self, value: float) -> None:
        self._vad.set_sensitivity(value)

    def set_language(self, lang_code: str) -> None:
        self._transcriber.set_language_mode(lang_code)

    def _capture_loop(self) -> None:
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
                logger.warning("Reabrindo fluxo de microfone após oscilação: %s", exc)
                if self._on_status:
                    self._on_status(f"Reconectando áudio: {exc}")
                time.sleep(0.2)

    def listen(self, idle_timeout: float = 1.0) -> str | None:
        """Consome frases da thread de captura; garante retorno str desempacotado."""
        if not self._worker.is_alive() and not self._stop_event.is_set():
            self._worker.start()
        deadline = time.monotonic() + idle_timeout
        while not self._stop_event.is_set() and time.monotonic() < deadline:
            try:
                audio, typed, dur, peak_rms = self._phrase_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            if typed:
                clean_typed, _ = unpack_transcription(typed)
                print("\n==========================================================================", flush=True)
                print(f"📋 [LOG CMD 1/4 - ENTRADA CAPTADA] Digitado no CMD: \"{clean_typed}\"", flush=True)
                print(f"📋 [LOG CMD 2/4 - LEITURA DA SUA FALA] Você disse: \"{clean_typed}\" (Motor: Teclado-CMD)", flush=True)
                return clean_typed

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

            try:
                raw_res = self._transcriber.transcribe(audio)
                text, engine = unpack_transcription(raw_res)
            except Exception as exc:
                logger.error("Erro na transcrição: %s", exc)
                if self._on_status:
                    self._on_status(f"Erro STT: {exc}")
                text, engine = "", "Erro"

            if text:
                if self._on_language_detected:
                    self._on_language_detected(self._transcriber.last_detected_language)
                self._dispatch_success(text, engine=engine)
                return text

            print("📋 [LOG CMD] ⚠️ Som sem fala nítida ignorado. Aguardando comando...", flush=True)
            if self._on_status:
                self._on_status("🟢 Ouvindo // Pode falar...")
        return None

    def _transcribe(self, audio: sr.AudioData) -> str | None:
        """Compatibilidade direta com Google STT para testes unitários."""
        try:
            res = self._recognizer.recognize_google(audio, language=self._language)
            text = str(res).strip() if res else ""
            if text:
                self._dispatch_success(text, engine="Google-Cloud")
                return text
        except (sr.UnknownValueError, sr.RequestError):
            pass
        return None

    def _dispatch_success(self, text: str, engine: str) -> None:
        print(f"📋 [LOG CMD 2/4 - LEITURA DA SUA FALA] Você falou: \"{text}\" (Motor: {engine})", flush=True)
        logger.info("🎙️ [STT] %s transcreveu: '%s'", engine, text)
        if self._on_status:
            self._on_status(f"Você disse: '{text}'")

    def close(self) -> None:
        self._stop_event.set()
