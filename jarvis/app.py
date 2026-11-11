"""Composição da aplicação: inicializa dependências, interface única (sem duplicação) e assistente."""

from __future__ import annotations

import ctypes
import logging
import sys
import threading
import tkinter as tk
from tkinter import messagebox

from jarvis.assistant import Assistant
from jarvis.commands import CommandContext, build_registry
from jarvis.config import ConfigError, Settings, load_settings
from jarvis.database.connection import DatabaseConnection
from jarvis.database.migrations import run_migrations
from jarvis.repositories.artifact_repository import ArtifactRepository
from jarvis.repositories.memory_repository import MemoryRepository
from jarvis.services.audio_effects import StarkSoundPlayer
from jarvis.services.autostart import disable_autostart
from jarvis.services.cognitive_engine import CognitiveEngine
from jarvis.services.conversation_session import ConversationSession
from jarvis.services.gemini_service import GeminiAnswerService
from jarvis.services.github_sync import sync_project_async
from jarvis.services.intent_cache import IntentCache
from jarvis.services.launcher import WindowsLauncher
from jarvis.services.message_store import TextFileMessageStore
from jarvis.services.process_manager import WindowsProcessManager
from jarvis.services.speech_corrector import SpeechCorrector
from jarvis.services.supabase_sync import SupabaseSyncService
from jarvis.services.terminal_bridge import TerminalBridge
from jarvis.services.wake_feedback import WakeFeedback
from jarvis.speech.listener import GoogleSpeechListener
from jarvis.speech.tts import build_speaker
from jarvis.ui.app_window import JarvisWindow

logger = logging.getLogger(__name__)

DIALOGUE_FOLLOW_UP_SECONDS = 10.0
_SINGLE_INSTANCE_MUTEX = None


class JarvisApplication:
    """Controla o ciclo de vida da aplicação e a thread única do assistente."""

    def __init__(self, root: tk.Tk, settings: Settings) -> None:
        self._settings = settings
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._speaker, self._listener, self._session = None, None, None
        self._gemini, self._assistant = None, None
        self._window = JarvisWindow(
            root, on_start=self.start, on_voice_change=self._handle_voice_change,
            on_device_selected=self._handle_device_change, on_sensitivity_change=self._handle_sensitivity_change,
            on_patience_change=self._handle_patience_change, on_language_change=self._handle_language_change,
            on_text_command=self._handle_text_command, on_interrupt=self._handle_interrupt,
        )
        root.protocol("WM_DELETE_WINDOW", lambda: self._close(root))

    def _handle_interrupt(self) -> None:
        if self._speaker and hasattr(self._speaker, "stop"):
            try:
                self._speaker.stop()
            except Exception:
                pass
        if self._session and hasattr(self._session, "close_dialogue"):
            self._session.close_dialogue()
        if self._assistant and hasattr(self._assistant, "stop"):
            self._assistant.stop()

    def _handle_text_command(self, text: str) -> None:
        if not self._assistant:
            return
        phrase = text if "jarvis" in text.lower() else f"jarvis {text}"
        threading.Thread(target=self._assistant.handle_phrase, args=(phrase,), daemon=True).start()

    def _handle_voice_change(self, profile: str) -> None:
        if self._speaker and hasattr(self._speaker, "set_voice"):
            self._speaker.set_voice(profile)

    def _handle_device_change(self, device_index: int) -> None:
        if self._listener:
            self._listener.set_device(device_index)

    def _handle_sensitivity_change(self, value: float) -> None:
        if self._listener and hasattr(self._listener, "set_sensitivity"):
            self._listener.set_sensitivity(value)

    def _handle_patience_change(self, seconds: float) -> None:
        if self._session:
            self._session.set_patience_seconds(seconds)

    def _handle_language_change(self, lang_code: str) -> None:
        if self._listener and hasattr(self._listener, "set_language"):
            self._listener.set_language(lang_code)
        if lang_code != "auto":
            self._apply_detected_language(lang_code)

    def _apply_detected_language(self, lang_code: str) -> None:
        if self._gemini and hasattr(self._gemini, "set_language"):
            self._gemini.set_language(lang_code)
        if self._speaker and hasattr(self._speaker, "set_language_voice"):
            self._speaker.set_language_voice(lang_code)

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run_assistant, name="jarvis-assistant", daemon=True)
        self._thread.start()

    def _run_assistant(self) -> None:
        settings = self._settings
        try:
            disable_autostart()
            sync_project_async()

            db = DatabaseConnection()
            run_migrations(db.get_connection())
            supabase = SupabaseSyncService(settings.supabase_url, settings.supabase_key)
            memory_repo = MemoryRepository(db, cloud_sync=supabase)
            artifact_repo = ArtifactRepository(db)
            intent_cache = IntentCache(memory_repo)
            corrector = SpeechCorrector()
            sounds = StarkSoundPlayer()
            session = ConversationSession(patience_seconds=DIALOGUE_FOLLOW_UP_SECONDS, silence_tolerance=2.2)
            self._session = session
            terminal = TerminalBridge()
            feedback = WakeFeedback(signal=self._window, sounds=sounds)

            from jarvis.services.user_profile import KEN_PROFILE
            KEN_PROFILE.sync_to_database(memory_repo)

            self._speaker = build_speaker(
                on_start=lambda: self._window.set_speaking(True),
                on_end=lambda: self._window.set_speaking(False),
            )
            gemini = GeminiAnswerService(settings.gemini_api_key, settings.gemini_model)
            self._gemini = gemini
            cognitive = CognitiveEngine(gemini, artifact_repo)

            self._listener = GoogleSpeechListener(
                language=settings.language, is_speaking=lambda: self._window.is_speaking,
                on_volume=self._window.update_mic_level, on_status=self._window.show_status,
                on_language_detected=self._apply_detected_language, on_interrupt=self._handle_interrupt,
                terminal=terminal, gemini=gemini,
            )
            ctx = CommandContext(
                speaker=self._speaker, listener=self._listener, view=self._window, answers=gemini,
                messages=TextFileMessageStore(settings.transcription_file), launcher=WindowsLauncher(),
                processes=WindowsProcessManager(), memory=memory_repo, artifacts=artifact_repo,
                cognitive=cognitive, session=session,
            )
            self._assistant = Assistant(
                ctx=ctx, wake_listener=self._listener, registry=build_registry(cache=intent_cache),
                user_name=settings.user_name, wake_word=settings.wake_word, stop_event=self._stop,
                corrector=corrector, sounds=sounds, session=session, terminal=terminal, feedback=feedback,
            )
            self._assistant.run()
        except Exception as exc:
            logger.exception("Falha ao inicializar o assistente: %s", exc)
            self._window.mark_stopped(error_message=f"Erro: {exc}")
        else:
            self._window.mark_stopped()

    def _close(self, root: tk.Tk) -> None:
        self._stop.set()
        root.destroy()


def main() -> None:
    """Garante instância única e inicializa a interface gráfica."""
    global _SINGLE_INSTANCE_MUTEX
    for stream in (sys.stdout, sys.stderr):
        try:
            if hasattr(stream, "reconfigure"):
                stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    try:
        _SINGLE_INSTANCE_MUTEX = ctypes.windll.kernel32.CreateMutexW(None, False, "JarvisStarkMarkVII_SingleInstance")
        if ctypes.windll.kernel32.GetLastError() == 183:
            raise SystemExit(0)
    except SystemExit:
        raise
    except Exception:
        pass
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    root = tk.Tk()
    try:
        settings = load_settings()
    except ConfigError as exc:
        root.withdraw()
        messagebox.showerror("J.A.R.V.I.S. - Configuração", str(exc))
        root.destroy()
        raise SystemExit(1) from exc
    JarvisApplication(root, settings)
    root.mainloop()
