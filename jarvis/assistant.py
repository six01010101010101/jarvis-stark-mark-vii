"""Orquestração de voz: ciclo de conversa ativa (15s), parada imediata por voz e ajuda ao chefe."""

from __future__ import annotations

from datetime import datetime
import logging
import random
import threading
from typing import TYPE_CHECKING, Callable

from jarvis.commands import CommandContext, CommandRegistry, Outcome
from jarvis.contracts import Listener
from jarvis.services.barge_in_listener import BargeInListener
from jarvis.services.conversation_session import ConversationSession
from jarvis.services.stark_personality import FIRST_WAKE_RESPONSE, SUBSEQUENT_WAKE_RESPONSES, TONY_STARK_GREETINGS, greeting_for
from jarvis.services.telemetry_recorder import async_persist_user_message, record_initial_telemetry
from jarvis.services.telemetry_state_machine import AssistantState, GLOBAL_STATE_MACHINE
from jarvis.services.voice_pipeline import RobustVoicePipeline
from jarvis.services.wake_feedback import WakeFeedback
from jarvis.speech.listener import MicrophoneError
from jarvis.speech.transcriber import unpack_transcription
from jarvis.text_utils import extract_wake_and_command, normalize, split_compound_commands

if TYPE_CHECKING:
    from jarvis.services.audio_effects import StarkSoundPlayer
    from jarvis.services.speech_corrector import SpeechCorrector

logger = logging.getLogger(__name__)

CLOSE_REPLY = "Às suas ordens, senhor. Conversa encerrada."
STOP_WORDS = (
    "jarvis pare", "pare jarvis", "pare de falar jarvis", "jarvis pare de falar",
    "jarvis para", "para jarvis", "para de falar jarvis", "silencio jarvis", "jarvis silencio",
    "stop jarvis", "jarvis stop", "pare", "parar", "para", "silencio", "silêncio", "cala a boca",
    "para de falar", "chega", "cancela",
)


class Assistant:
    """Escuta 'Jarvis', atende com estilo de amigo, suporta conversa ativa (15s) e interrupção por voz."""

    def __init__(
        self,
        ctx: CommandContext,
        wake_listener: Listener,
        registry: CommandRegistry,
        user_name: str,
        wake_word: str,
        stop_event: threading.Event,
        corrector: SpeechCorrector | None = None,
        sounds: StarkSoundPlayer | None = None,
        session: ConversationSession | None = None,
        terminal: object | None = None,
        clock: Callable[[], datetime] = datetime.now,
        choose: Callable[[tuple[str, ...]], str] = random.choice,
        feedback: WakeFeedback | None = None,
    ) -> None:
        self._ctx, self._wake_listener = ctx, wake_listener
        self._registry, self._user_name = registry, user_name
        self._wake_word, self._stop = normalize(wake_word), stop_event
        self._corrector, self._sounds = corrector, sounds
        self._strict_wake = session is not None
        self._session = session or ConversationSession(timeout_seconds=15.0, patience_seconds=15.0, silence_tolerance=2.2)
        self._terminal, self._clock, self._choose = terminal, clock, choose
        self._feedback = feedback or WakeFeedback(sounds=sounds)
        self._last_mode: bool | None = None
        self._wake_count = 0
        self.pipeline = RobustVoicePipeline(self)
        self.barge_in = BargeInListener(on_stop_callback=self.stop)

    def introduce(self) -> None:
        if self._sounds:
            self._sounds.play_boot()
        if self._terminal and hasattr(self._terminal, "print_hud_banner"):
            self._terminal.print_hud_banner(
                getattr(self._wake_listener, "device_name", "Microfone Padrão"),
                getattr(self._wake_listener, "sample_rate", 16000),
                getattr(self._wake_listener, "_device_index", None),
            )
        threading.Thread(target=record_initial_telemetry, args=(self._ctx.memory,), daemon=True).start()
        intro = f"Bem-vindo, {self._user_name}." if self._user_name.strip().lower() == "ken" else self._choose(TONY_STARK_GREETINGS).format(greeting=greeting_for(self._clock().hour), user=self._user_name)
        self._ctx.view.show_status(intro)
        if hasattr(self._ctx.view, "append_chat"):
            self._ctx.view.append_chat("assistant", intro)
        threading.Thread(target=self._ctx.speaker.say, args=(intro,), daemon=True).start()

    def stop(self) -> None:
        """Interrompe a fala atual imediatamente por voz ('Jarvis, pare') e encerra diálogo."""
        if hasattr(self._ctx.speaker, "stop"):
            try:
                self._ctx.speaker.stop()
            except Exception:
                pass
        self._session.close_dialogue()
        self._ctx.view.show_status("PARADO // SILENCIANDO")
        self._feedback.sync(dialogue_active=False)

    def handle_phrase(self, phrase: str | tuple[str, str]) -> Outcome:
        raw_text, _ = unpack_transcription(phrase)
        if not raw_text:
            return Outcome.CONTINUE

        clean_norm = normalize(raw_text)
        if self.barge_in.is_stop_phrase(clean_norm) or any(clean_norm == s for s in STOP_WORDS):
            self.stop()
            return Outcome.CONTINUE

        corrected = self._corrector.correct(raw_text) if self._corrector else raw_text
        is_wake, inline_cmd = extract_wake_and_command(corrected, self._wake_word)
        in_patience = self._session.should_listen_without_wake_word()

        if self._strict_wake and not is_wake and not in_patience:
            self._feedback.ignored_in_standby(corrected)
            return Outcome.CONTINUE

        if hasattr(self._ctx.view, "append_chat"):
            self._ctx.view.append_chat("user", corrected)
        threading.Thread(target=async_persist_user_message, args=(self._ctx, corrected), daemon=True).start()

        if self._session.is_close_phrase(corrected):
            self.stop()
            self._ctx.reply(CLOSE_REPLY)
            self._session.close_dialogue()
            return Outcome.CONTINUE

        if is_wake and ConversationSession.is_assistance_trigger(corrected):
            self._wake_count += 1
            self._feedback.wake_heard(corrected)
            self._ctx.reply("Sim, no que eu posso te ajudar, chefe?")
            self._session.start_dialogue(awaiting_answer=True)
            self._session.activate_patience_window()
            self._ctx.view.show_status("🟢 CONVERSA ATIVA (15s) // PODE FALAR")
            self._feedback.dialogue_open()
            return Outcome.CONTINUE

        if is_wake and not inline_cmd:
            self._wake_count += 1
            self._feedback.wake_heard(corrected)
            wake_reply = FIRST_WAKE_RESPONSE if self._wake_count == 1 else self._choose(SUBSEQUENT_WAKE_RESPONSES)
            self._ctx.reply(wake_reply)
            self._session.start_dialogue(awaiting_answer=True)
            self._session.activate_patience_window()
            self._feedback.dialogue_open()
            return Outcome.CONTINUE

        if is_wake:
            self._feedback.wake_heard(corrected)
        cmd_text = inline_cmd if (is_wake and inline_cmd) else corrected
        resolved_cmd = self._session.resolve_utterance_with_pending(cmd_text)
        GLOBAL_STATE_MACHINE.transition_to(AssistantState.PROCESSING, "executing_command")
        outcome = Outcome.CONTINUE
        for sub_cmd in split_compound_commands(resolved_cmd):
            outcome = self._registry.dispatch(self._ctx, sub_cmd)
            if outcome is Outcome.SHUTDOWN:
                break
        if self._sounds and outcome is Outcome.CONTINUE:
            self._sounds.play_ping()

        if self._session.get_pending_intent() is not None or self._session.is_awaiting_answer():
            self._session.activate_patience_window()
            self._feedback.dialogue_open()
        else:
            self._session.close_dialogue()
            GLOBAL_STATE_MACHINE.transition_to(AssistantState.LISTENING, "standby_wake_word")
            self._ctx.view.show_status("EM ESPERA // DIGA \"JARVIS\" PARA ATIVAR")
            self._feedback.sync(dialogue_active=False)
        return outcome

    def _refresh_mode(self) -> None:
        in_dialogue = self._session.should_listen_without_wake_word()
        self._feedback.sync(dialogue_active=in_dialogue)
        if in_dialogue == self._last_mode:
            return
        self._last_mode = in_dialogue
        if in_dialogue:
            GLOBAL_STATE_MACHINE.transition_to(AssistantState.PATIENCE_WAIT, "patience_active")
            rem = int(self._session.remaining_patience() or self._session.patience_seconds)
            self._ctx.view.show_status(f"🟢 CONVERSA ATIVA ({rem}s) // PODE FALAR SEU PEDIDO")
        else:
            GLOBAL_STATE_MACHINE.transition_to(AssistantState.LISTENING, "standby_wake_word")
            self._ctx.view.show_status("EM ESPERA // DIGA \"JARVIS\" PARA ATIVAR")

    def run(self) -> None:
        try:
            self.introduce()
            while not self._stop.is_set():
                self._refresh_mode()
                try:
                    phrase = self._wake_listener.listen()
                    if phrase is None and self._ctx.listener is not self._wake_listener:
                        phrase = self._ctx.listener.listen()
                        if phrase is None:
                            break
                    if phrase and self.handle_phrase(phrase) is Outcome.SHUTDOWN:
                        break
                except MicrophoneError as mic_err:
                    GLOBAL_STATE_MACHINE.transition_to(AssistantState.ERROR, "mic_unavailable")
                    self._ctx.view.show_status(f"Reconectando microfone: {mic_err}")
                except Exception as exc:
                    GLOBAL_STATE_MACHINE.transition_to(AssistantState.ERROR, str(exc))
                    self._ctx.view.show_status(f"Alerta no ciclo: {exc}")
        finally:
            self._stop.set()
