"""Orquestração do assistente: ativação por 'Jarvis', Ciclo de Paciência (10s) e DB Fire-and-Forget."""

from __future__ import annotations

from datetime import datetime
import logging
import random
import threading
from typing import TYPE_CHECKING, Callable

from jarvis.commands import CommandContext, CommandRegistry, Outcome
from jarvis.contracts import Listener
from jarvis.services.conversation_session import ConversationSession
from jarvis.services.stark_personality import TONY_STARK_GREETINGS, WAKE_PROMPT, WAKE_RESPONSES, greeting_for
from jarvis.services.telemetry_state_machine import AssistantState, GLOBAL_STATE_MACHINE
from jarvis.services.wake_feedback import WakeFeedback
from jarvis.speech.listener import MicrophoneError
from jarvis.text_utils import extract_wake_and_command, normalize, split_compound_commands

if TYPE_CHECKING:
    from jarvis.services.audio_effects import StarkSoundPlayer
    from jarvis.services.speech_corrector import SpeechCorrector

logger = logging.getLogger(__name__)

CLOSE_REPLY = "Às suas ordens, senhor. Conversa encerrada."


class Assistant:
    """Escuta 'Jarvis', responde com latência zero de banco e mantém Ciclo de Paciência de 10s."""

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
        self._session = session or ConversationSession(patience_seconds=10.0, silence_tolerance=2.2)
        self._terminal, self._clock, self._choose = terminal, clock, choose
        self._feedback = feedback or WakeFeedback(sounds=sounds)
        self._last_mode: bool | None = None

    def introduce(self) -> None:
        if self._sounds:
            self._sounds.play_boot()

        if self._terminal and hasattr(self._terminal, "print_hud_banner"):
            self._terminal.print_hud_banner(
                getattr(self._wake_listener, "device_name", "Microfone Padrão"),
                getattr(self._wake_listener, "sample_rate", 16000),
                getattr(self._wake_listener, "_device_index", None),
            )

        if self._ctx.memory and hasattr(self._ctx.memory, "record_telemetry_snapshot"):
            threading.Thread(
                target=self._record_initial_telemetry,
                name="telemetry-init-async",
                daemon=True,
            ).start()

        greeting = greeting_for(self._clock().hour)
        intro_text = self._choose(TONY_STARK_GREETINGS).format(greeting=greeting, user=self._user_name)
        print(f"\n[CMD-JARVIS] 🤖 Saudação Inicial: \"{intro_text}\"", flush=True)
        self._ctx.view.show_status(intro_text)
        t_intro = threading.Thread(target=self._ctx.speaker.say, args=(intro_text,), daemon=True)
        t_intro.start()
        t_intro.join(timeout=0.05)

    def _record_initial_telemetry(self) -> None:
        try:
            snap = self._ctx.memory.record_telemetry_snapshot()  # type: ignore[union-attr]
            print(
                f"[TELEMETRIA-SQLITE] 📊 RAM: {snap.get('ram_used_gb')}GB usada / "
                f"{snap.get('ram_free_gb')}GB livre | Disco C: {snap.get('disk_free_gb')}GB livre",
                flush=True,
            )
        except Exception as exc:  # noqa: BLE001
            logger.debug("Telemetria inicial indisponível: %s", exc)

    def _async_persist_user_message(self, text: str) -> None:
        """Grava fala do usuário no SQLite, Supabase e arquivo em background (Fire-and-Forget)."""
        from jarvis.commands.privacy_commands import is_private_mode
        from jarvis.services.rolling_transcript import GLOBAL_TRANSCRIPT

        if is_private_mode():
            return
        GLOBAL_TRANSCRIPT.add_turn("user", text)
        if self._ctx.memory:
            if hasattr(self._ctx.memory, "record_message_async"):
                self._ctx.memory.record_message_async("user", text)
            else:
                self._ctx.memory.record_message("user", text)
        try:
            if hasattr(self._ctx.messages, "save_async"):
                self._ctx.messages.save_async(text)  # type: ignore[attr-defined]
            else:
                self._ctx.messages.save(text)
        except Exception as exc:
            logger.debug("Aviso ao salvar transcrição: %s", exc)

    def _on_speech_finished(self) -> None:
        """Aciona o Ciclo de Paciência (10s) assim que o Jarvis termina de falar."""
        self._session.activate_patience_window()
        GLOBAL_STATE_MACHINE.transition_to(AssistantState.PATIENCE_WAIT, "patience_cycle")
        self._ctx.view.show_status(f"🟢 CICLO DE PACIÊNCIA ({int(self._session.patience_seconds)}s) // PODE FALAR")

    def _execute_command_or_compound(self, command_text: str) -> Outcome:
        GLOBAL_STATE_MACHINE.transition_to(AssistantState.PROCESSING, "executing_command")
        outcome = Outcome.CONTINUE
        for sub_cmd in split_compound_commands(command_text):
            outcome = self._registry.dispatch(self._ctx, sub_cmd)
            if outcome is Outcome.SHUTDOWN:
                break
        if self._sounds and outcome is Outcome.CONTINUE:
            self._sounds.play_ping()
        return outcome

    def handle_phrase(self, phrase: str) -> Outcome:
        """Processa a fala com persistência Fire-and-Forget e Ciclo de Paciência Inteligente."""
        corrected = self._corrector.correct(phrase) if self._corrector else phrase
        is_wake, inline_cmd = extract_wake_and_command(corrected, self._wake_word)

        if self._strict_wake and not is_wake and not self._session.should_listen_without_wake_word():
            self._feedback.ignored_in_standby(corrected)
            return Outcome.CONTINUE

        # Persistência Fire-and-Forget em thread daemon (0ms de bloqueio)
        threading.Thread(
            target=self._async_persist_user_message,
            args=(corrected,),
            name="user-msg-async",
            daemon=True,
        ).start()
        print(
            f"📋 [LOG CMD 3/4 - LEITURA DO JARVIS & SQLITE] Jarvis leu: \"{corrected}\" -> Fire-and-Forget!",
            flush=True,
        )

        if self._session.is_close_phrase(corrected):
            self._session.close_dialogue()
            self._ctx.reply(CLOSE_REPLY)
            self._session.close_dialogue()
            self._feedback.sync(dialogue_active=False)
            return Outcome.CONTINUE

        if is_wake and not inline_cmd:
            self._feedback.wake_heard(corrected)
            self._session.start_dialogue(awaiting_answer=True)
            self._ctx.reply(self._choose(WAKE_RESPONSES) if WAKE_RESPONSES else WAKE_PROMPT)
            self._session.start_dialogue(awaiting_answer=True)
            self._feedback.dialogue_open()
            return Outcome.CONTINUE

        if is_wake:
            self._feedback.wake_heard(corrected)
        cmd_text = inline_cmd if (is_wake and inline_cmd) else corrected
        resolved_cmd = self._session.resolve_utterance_with_pending(cmd_text)
        outcome = self._execute_command_or_compound(resolved_cmd)

        if self._session.is_awaiting_answer():
            self._feedback.dialogue_open()
        else:
            self._on_speech_finished()
            self._feedback.sync(dialogue_active=self._session.is_active())
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
            self._ctx.view.show_status(f"🟢 CICLO DE PACIÊNCIA ({rem}s) // PODE FALAR SEU PEDIDO")
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
                    logger.warning("Microfone indisponível: %s", mic_err)
                    self._ctx.view.show_status("Reconectando microfone...")
                except Exception as exc:  # noqa: BLE001
                    GLOBAL_STATE_MACHINE.transition_to(AssistantState.ERROR, str(exc))
                    logger.exception("Erro no ciclo do assistente: %s", exc)
        finally:
            self._stop.set()
