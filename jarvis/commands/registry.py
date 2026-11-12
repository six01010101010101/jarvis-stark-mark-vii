"""Estruturas centrais de comandos: contexto protegido, resultado e registro seguro."""

from __future__ import annotations

import ctypes
from dataclasses import dataclass, field
from enum import Enum, auto
import threading
from typing import TYPE_CHECKING, Callable

from jarvis.contracts import (
    AnswerProvider,
    CognitiveService,
    Listener,
    MessageStore,
    ProcessController,
    ProgramLauncher,
    Speaker,
    StatusView,
)
from jarvis.security.security_guard import SecurityGuard
from jarvis.services.conversation_session import ConversationSession
from jarvis.text_utils import normalize

if TYPE_CHECKING:
    from jarvis.repositories.artifact_repository import ArtifactRepository
    from jarvis.repositories.memory_repository import MemoryRepository
    from jarvis.services.intent_cache import IntentCache


class Outcome(Enum):
    """Resultado da execução de um comando."""

    CONTINUE = auto()
    SHUTDOWN = auto()


@dataclass(frozen=True)
class CommandContext:
    """Dependências disponíveis para os comandos com proteção cibernética integrada."""

    speaker: Speaker
    listener: Listener
    view: StatusView
    answers: AnswerProvider
    messages: MessageStore
    launcher: ProgramLauncher
    processes: ProcessController
    memory: MemoryRepository | None = None
    artifacts: ArtifactRepository | None = None
    cognitive: CognitiveService | None = None
    session: object | None = None

    def _persist_reply_async(self, text: str) -> None:
        try:
            if self.memory:
                if hasattr(self.memory, "record_message_async"):
                    self.memory.record_message_async("assistant", text)
                else:
                    self.memory.record_message("assistant", text)
        except Exception:
            pass

    def reply(self, text: str, pending_intent: str | None = None) -> None:
        """Dispara áudio higienizado no ms 0 sem vazar dados sigilosos e abre ciclo de paciência."""
        from jarvis.services.rolling_transcript import GLOBAL_TRANSCRIPT
        from jarvis.services.telemetry_state_machine import AssistantState, GLOBAL_STATE_MACHINE

        safe_text = SecurityGuard.redact_secrets(text)
        GLOBAL_STATE_MACHINE.transition_to(AssistantState.SPEAKING, "replying")
        GLOBAL_TRANSCRIPT.add_turn("assistant", safe_text)
        print(f"📋 [LOG CMD 4/4 - RESPOSTA] 🤖 J.A.R.V.I.S.: \"{safe_text}\"", flush=True)
        self.view.show_status(safe_text)
        if hasattr(self.view, "append_chat"):
            self.view.append_chat("assistant", safe_text)

        if self.session and hasattr(self.session, "mark_interaction"):
            self.session.mark_interaction(awaiting_answer=pending_intent is not None, pending_intent=pending_intent)

        threading.Thread(target=self._persist_reply_async, args=(safe_text,), name="reply-db-async", daemon=True).start()
        self.speaker.say(safe_text)

        if pending_intent is not None and self.session and hasattr(self.session, "activate_patience_window"):
            self.session.activate_patience_window()
            GLOBAL_STATE_MACHINE.transition_to(AssistantState.PATIENCE_WAIT, "patience_cycle")
        else:
            GLOBAL_STATE_MACHINE.transition_to(AssistantState.LISTENING, "turn_completed")


Handler = Callable[[CommandContext, str], Outcome]


@dataclass(frozen=True)
class Command:
    """Um comando de voz: frases-gatilho + função que o executa."""

    name: str
    triggers: tuple[str, ...]
    handler: Handler

    def matches(self, utterance: str) -> bool:
        spoken = normalize(utterance)
        return any(normalize(trigger) in spoken for trigger in self.triggers)


@dataclass
class CommandRegistry:
    """Coleção de comandos com cache preditivo e inspeção defensiva de injeção."""

    commands: list[Command] = field(default_factory=list)
    cache: IntentCache | None = None

    def register(self, *commands: Command) -> None:
        self.commands.extend(commands)

    def find(self, utterance: str) -> Command | None:
        return next((cmd for cmd in self.commands if cmd.matches(utterance)), None)

    def _execute_intent(self, ctx: CommandContext, intent: dict[str, str]) -> None:
        action = intent.get("action", "chat")
        target = intent.get("target", "")
        reply = intent.get("reply", "")

        if not SecurityGuard.is_safe_shell_input(target):
            ctx.reply("Comando bloqueado pelo protocolo de cibersegurança do Stark Shield.")
            return

        safe_target = SecurityGuard.sanitize_command_argument(target)
        if action == "open_url" and safe_target:
            if reply:
                ctx.reply(reply)
            ctx.launcher.open_url(safe_target)
            if ctx.session and hasattr(ctx.session, "close_dialogue"):
                ctx.session.close_dialogue()
            return

        if action == "open_app" and safe_target:
            if reply:
                ctx.reply(reply)
            ctx.launcher.launch(safe_target)
            if ctx.session and hasattr(ctx.session, "close_dialogue"):
                ctx.session.close_dialogue()
            return

        if action == "close_tab":
            ctypes.windll.user32.keybd_event(0x11, 0, 0, 0)
            ctypes.windll.user32.keybd_event(0x57, 0, 0, 0)
            ctypes.windll.user32.keybd_event(0x57, 0, 0x0002, 0)
            ctypes.windll.user32.keybd_event(0x11, 0, 0x0002, 0)
            ctx.reply(reply or "Aba do navegador encerrada, senhor.")
            if ctx.session and hasattr(ctx.session, "close_dialogue"):
                ctx.session.close_dialogue()
            return

        if action == "close_window":
            ctypes.windll.user32.keybd_event(0x12, 0, 0, 0)
            ctypes.windll.user32.keybd_event(0x73, 0, 0, 0)
            ctypes.windll.user32.keybd_event(0x73, 0, 0x0002, 0)
            ctypes.windll.user32.keybd_event(0x12, 0, 0x0002, 0)
            ctx.reply(reply or "Janela encerrada, senhor.")
            if ctx.session and hasattr(ctx.session, "close_dialogue"):
                ctx.session.close_dialogue()
            return

        if action == "close_app" and safe_target:
            ctx.processes.close_app(safe_target)
            if reply:
                ctx.reply(reply)
            if ctx.session and hasattr(ctx.session, "close_dialogue"):
                ctx.session.close_dialogue()
            return

        ctx.reply(reply if reply else "Não compreendi o comando, senhor.")

    def dispatch(self, ctx: CommandContext, utterance: str) -> Outcome:
        """Executa comando de forma segura, com validação de payload e tratamento inteligente."""
        is_valid, reason = SecurityGuard.validate_chat_input(utterance)
        if not is_valid:
            ctx.reply(f"Comando rejeitado por segurança: {reason}")
            return Outcome.CONTINUE

        command = self.find(utterance)
        if command is not None:
            return command.handler(ctx, utterance)

        if self.cache:
            cached = self.cache.get(utterance)
            if cached and cached.get("action") in ("open_url", "open_app", "close_app"):
                self._execute_intent(ctx, cached)
                return Outcome.CONTINUE

        complexity = ConversationSession.evaluate_query_complexity(utterance)
        if complexity == "DEEP" and hasattr(ctx.speaker, "speak_thinking_filler"):
            ctx.view.show_status("🧠 RACIOCINANDO PROFUNDO // CONSULTANDO DADOS...")
            ctx.speaker.speak_thinking_filler()

        try:
            intent = ctx.answers.interpret_intent(utterance)
            action = intent.get("action", "chat")
            reply = intent.get("reply", "")
            if self.cache and action in ("open_url", "open_app", "close_app"):
                self.cache.put(utterance, action, intent.get("target", ""), reply)
            elif ctx.memory and action == "chat" and reply and len(utterance.strip()) >= 8:
                ctx.memory.remember(f"qa:{normalize(utterance)[:80]}", reply, "knowledge")
            self._execute_intent(ctx, intent)
        except Exception:
            ctx.reply(f"Não consegui processar o pedido '{utterance}', senhor.")
        return Outcome.CONTINUE
