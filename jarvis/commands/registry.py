"""Estruturas centrais do sistema de comandos: contexto Fire-and-Forget, resultado e registro com cache."""

from __future__ import annotations

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
    """Dependências disponíveis para os comandos com disparo de voz prioritário (0ms DB delay)."""

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
        """Persiste a resposta no SQLite e nuvem em background sem atrasar a voz."""
        try:
            if self.memory:
                if hasattr(self.memory, "record_message_async"):
                    self.memory.record_message_async("assistant", text)
                else:
                    self.memory.record_message("assistant", text)
        except Exception:
            pass

    def reply(self, text: str, pending_intent: str | None = None) -> None:
        """Dispara o áudio no milissegundo 0 em paralelo com o banco de dados e abre Ciclo de Paciência."""
        from jarvis.services.rolling_transcript import GLOBAL_TRANSCRIPT
        from jarvis.services.telemetry_state_machine import AssistantState, GLOBAL_STATE_MACHINE

        GLOBAL_STATE_MACHINE.transition_to(AssistantState.SPEAKING, "replying")
        GLOBAL_TRANSCRIPT.add_turn("assistant", text)
        print(f"📋 [LOG CMD 4/4 - RESPOSTA DO JARVIS] 🤖 J.A.R.V.I.S.: \"{text}\"", flush=True)
        print("==========================================================================\n", flush=True)
        self.view.show_status(text)
        if hasattr(self.view, "append_chat"):
            self.view.append_chat("assistant", text)

        if self.session and hasattr(self.session, "mark_interaction"):
            is_question = text.strip().endswith("?")
            self.session.mark_interaction(awaiting_answer=is_question, pending_intent=pending_intent)

        # 1. Gravação Fire-and-Forget no SQLite e Supabase em thread daemon
        threading.Thread(target=self._persist_reply_async, args=(text,), name="reply-db-async", daemon=True).start()

        # 2. Disparo imediato da voz (Prioridade Zero!)
        self.speaker.say(text)

        # 3. Inicia o Ciclo de Paciência (10s) pós-fala
        if self.session and hasattr(self.session, "activate_patience_window"):
            self.session.activate_patience_window()
        GLOBAL_STATE_MACHINE.transition_to(AssistantState.PATIENCE_WAIT, "patience_cycle")


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
    """Coleção ordenada de comandos com cache preditivo de 0ms e intuição de complexidade."""

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

        if action == "open_url" and target:
            ctx.launcher.open_url(target)
            if reply:
                ctx.reply(reply)
            return

        if action == "open_app" and target:
            ctx.launcher.launch(target)
            if reply:
                ctx.reply(reply)
            return

        if action == "close_tab":
            import ctypes
            ctypes.windll.user32.keybd_event(0x11, 0, 0, 0)
            ctypes.windll.user32.keybd_event(0x57, 0, 0, 0)
            ctypes.windll.user32.keybd_event(0x57, 0, 0x0002, 0)
            ctypes.windll.user32.keybd_event(0x11, 0, 0x0002, 0)
            ctx.reply(reply or "Aba do navegador encerrada, senhor.")
            return

        if action == "close_window":
            import ctypes
            ctypes.windll.user32.keybd_event(0x12, 0, 0, 0)
            ctypes.windll.user32.keybd_event(0x73, 0, 0, 0)
            ctypes.windll.user32.keybd_event(0x73, 0, 0x0002, 0)
            ctypes.windll.user32.keybd_event(0x12, 0, 0x0002, 0)
            ctx.reply(reply or "Janela encerrada, senhor.")
            return

        if action == "close_app" and target:
            ctx.processes.close_app(target)
            if reply:
                ctx.reply(reply)
            return

        ctx.reply(reply if reply else "Não compreendi o comando, senhor.")

    def dispatch(self, ctx: CommandContext, utterance: str) -> Outcome:
        """Executa comando rápido (<1.5s), consulta cache (0ms) ou aciona raciocínio profundo."""
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
        except Exception:  # noqa: BLE001
            ctx.reply(f"Não consegui processar o pedido '{utterance}', senhor.")
        return Outcome.CONTINUE
