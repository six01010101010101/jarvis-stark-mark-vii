"""Estruturas centrais do sistema de comandos: contexto, resultado e registro com cache."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
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
    """Dependências disponíveis para os comandos."""

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

    def reply(self, text: str, pending_intent: str | None = None) -> None:
        """Mostra o texto na interface, no CMD e o fala."""
        from jarvis.services.rolling_transcript import GLOBAL_TRANSCRIPT
        from jarvis.services.telemetry_state_machine import AssistantState, GLOBAL_STATE_MACHINE

        GLOBAL_STATE_MACHINE.transition_to(AssistantState.SPEAKING, "replying")
        GLOBAL_TRANSCRIPT.add_turn("assistant", text)
        if self.memory:
            self.memory.record_message("assistant", text)
        print(f"📋 [LOG CMD 4/4 - RESPOSTA DO JARVIS] 🤖 J.A.R.V.I.S.: \"{text}\"", flush=True)
        print("==========================================================================\n", flush=True)
        self.view.show_status(text)
        if self.session and hasattr(self.session, "mark_interaction"):
            is_question = text.strip().endswith("?")
            self.session.mark_interaction(awaiting_answer=is_question, pending_intent=pending_intent)
        self.speaker.say(text)



Handler = Callable[[CommandContext, str], Outcome]


@dataclass(frozen=True)
class Command:
    """Um comando de voz: frases-gatilho + função que o executa."""

    name: str
    triggers: tuple[str, ...]
    handler: Handler

    def matches(self, utterance: str) -> bool:
        """Retorna True se algum gatilho aparece na fala (ignora maiúsculas e acentos)."""
        spoken = normalize(utterance)
        return any(normalize(trigger) in spoken for trigger in self.triggers)


@dataclass
class CommandRegistry:
    """Coleção ordenada de comandos com cache preditivo de 0ms para alta velocidade."""

    commands: list[Command] = field(default_factory=list)
    cache: IntentCache | None = None

    def register(self, *commands: Command) -> None:
        """Adiciona comandos ao registro."""
        self.commands.extend(commands)

    def find(self, utterance: str) -> Command | None:
        """Encontra o comando correspondente à fala, ou None."""
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

        if reply:
            ctx.reply(reply)
        else:
            ctx.reply("Não compreendi o comando, senhor.")

    def dispatch(self, ctx: CommandContext, utterance: str) -> Outcome:
        """Executa comando imediato, consulta cache (0ms) ou Gemini/Internet para intenções e perguntas."""
        command = self.find(utterance)
        if command is not None:
            return command.handler(ctx, utterance)

        # 1. Verifica cache de alta velocidade para ações de sistema
        if self.cache:
            cached = self.cache.get(utterance)
            if cached and cached.get("action") in ("open_url", "open_app", "close_app"):
                self._execute_intent(ctx, cached)
                return Outcome.CONTINUE

        # 2. IA + Fontes Web (Google/Wikipedia/Clima) + SQLite analisam a intenção ou pergunta
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
