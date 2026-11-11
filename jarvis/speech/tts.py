"""Síntese de voz limpa e cinematográfica (Edge-TTS pt-BR) com streaming por frases e SAPI5."""

from __future__ import annotations

import logging
import queue
import re
import threading
from typing import Callable

from jarvis.contracts import Speaker

logger = logging.getLogger(__name__)


class NativeWindowsSpeaker(Speaker):
    """Sintetizador de voz nativo do Windows (SAPI5 / Microsoft Speech) com fila de sentenças."""

    def __init__(
        self,
        on_start: Callable[[], None],
        on_end: Callable[[], None],
    ) -> None:
        self._on_start = on_start
        self._on_end = on_end
        self._lock = threading.Lock()
        self._profile = "male"
        self._voice: object = None
        self._pyttsx_engine: object = None
        self._queue: queue.Queue[tuple[str, Callable[[], None] | None]] = queue.Queue()
        self.is_speaking = False
        self._init_voice()

    def _init_voice(self) -> None:
        try:
            import comtypes
            comtypes.CoInitialize()
            import comtypes.client
            self._voice = comtypes.client.CreateObject("SAPI.SpVoice")
            self._voice.Rate = 2  # type: ignore[attr-defined]
            self._voice.Volume = 100  # type: ignore[attr-defined]
            self.set_voice(self._profile)
            logger.info("🎙️ [TTS] SAPI5 inicializado com sucesso via comtypes.")
        except Exception as exc:
            logger.warning("Falha ao inicializar SAPI via comtypes (%s). Ativando pyttsx3 fallback.", exc)
            self._voice = None
            try:
                import pyttsx3
                self._pyttsx_engine = pyttsx3.init()
                self._pyttsx_engine.setProperty("rate", 215)  # type: ignore[attr-defined]
            except Exception as e2:
                logger.error("Falha ao inicializar pyttsx3: %s", e2)
                self._pyttsx_engine = None

    def set_voice(self, profile: str) -> bool:
        """Alterna entre voz masculina (Daniel/David) e feminina (Maria)."""
        self._profile = "female" if any(w in profile.lower() for w in ("fem", "maria", "mulher")) else "male"
        is_female = self._profile == "female"

        if self._voice is not None:
            try:
                voices = list(self._voice.GetVoices())  # type: ignore[attr-defined]
                for v in voices:
                    desc = v.GetDescription().lower()
                    if is_female and any(k in desc for k in ("maria", "zira", "female", "helena")):
                        self._voice.Voice = v  # type: ignore[attr-defined]
                        return True
                    elif not is_female and any(k in desc for k in ("daniel", "david", "male", "george", "mark")):
                        self._voice.Voice = v  # type: ignore[attr-defined]
                        return True
                if not is_female and voices:
                    for v in voices:
                        desc = v.GetDescription().lower()
                        if not any(k in desc for k in ("maria", "zira", "female", "helena")):
                            self._voice.Voice = v  # type: ignore[attr-defined]
                            return True
            except Exception as exc:
                logger.debug("Erro ao selecionar voz SAPI: %s", exc)

        if self._pyttsx_engine is not None:
            try:
                voices = list(self._pyttsx_engine.getProperty("voices"))  # type: ignore[attr-defined]
                for v in voices:
                    desc = f"{v.id} {v.name}".lower()
                    if is_female and any(k in desc for k in ("maria", "zira", "female", "helena")):
                        self._pyttsx_engine.setProperty("voice", v.id)  # type: ignore[attr-defined]
                        return True
                    elif not is_female and any(k in desc for k in ("daniel", "david", "male", "george", "mark")):
                        self._pyttsx_engine.setProperty("voice", v.id)  # type: ignore[attr-defined]
                        return True
            except Exception:
                pass

        return False

    def get_voice(self) -> str:
        return "Daniel (Masculina)" if self._profile == "male" else "Maria (Feminina)"

    def set_language_voice(self, lang_code: str) -> str:
        """Compatibilidade Poliglota com motor nativo."""
        return self.get_voice()

    def speak(self, text: str) -> None:
        """Compatibilidade direta com NeuralSpeakerStream."""
        self.say(text)

    def speak_async(self, text: str, on_complete: Callable[[], None] | None = None) -> None:
        """Reproduz por sentenças em background."""
        chunks = [c.strip() for c in re.split(r"(?<=[.!?।:;])\s+", text.strip()) if c.strip()]

        def _worker() -> None:
            for ch in chunks:
                self.say(ch)
            if on_complete:
                on_complete()

        threading.Thread(target=_worker, name="sapi-stream", daemon=True).start()

    def say(self, text: str) -> None:
        """Fala a frase de forma síncrona, direta e sem deadlocks."""
        clean = text.strip()
        if not clean:
            return

        with self._lock:
            self.is_speaking = True
            try:
                import comtypes
                comtypes.CoInitialize()
            except Exception:
                pass

            if self._voice is None and self._pyttsx_engine is None:
                self._init_voice()

            self._on_start()
            try:
                if self._voice is not None:
                    self._voice.Speak(clean, 0)  # type: ignore[attr-defined]
                elif self._pyttsx_engine is not None:
                    self._pyttsx_engine.say(clean)  # type: ignore[attr-defined]
                    self._pyttsx_engine.runAndWait()  # type: ignore[attr-defined]
            except Exception as exc:
                logger.error("Erro durante síntese de voz: %s", exc)
            finally:
                self.is_speaking = False
                self._on_end()


PyttsxSpeaker = NativeWindowsSpeaker
WinRTSpeaker = NativeWindowsSpeaker


def build_speaker(on_start: Callable[[], None], on_end: Callable[[], None]) -> Speaker:
    """Retorna o sintetizador com voz limpa (Edge-TTS), streaming por frases e fallback nativo."""
    from jarvis.services.neural_speaker import NeuralSpeaker
    native_fallback = NativeWindowsSpeaker(on_start=lambda: None, on_end=lambda: None)
    return NeuralSpeaker(fallback=native_fallback, on_start=on_start, on_end=on_end)
