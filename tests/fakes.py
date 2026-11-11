"""Dublês de teste que implementam os contratos do assistente."""

from __future__ import annotations

from dataclasses import dataclass, field

from jarvis.commands import CommandContext
from jarvis.contracts import AnswerServiceError, LaunchError


@dataclass
class FakeSpeaker:
    spoken: list[str] = field(default_factory=list)
    current_voice: str = "male"

    def say(self, text: str) -> None:
        self.spoken.append(text)

    def stop(self) -> None:
        pass

    def set_voice(self, profile: str) -> bool:
        self.current_voice = profile
        return True

    def get_voice(self) -> str:
        return self.current_voice



@dataclass
class FakeListener:
    answers: list[str | None] = field(default_factory=list)

    def listen(self) -> str | None:
        return self.answers.pop(0) if self.answers else None


@dataclass
class FakeView:
    statuses: list[str] = field(default_factory=list)
    speaking: bool = False

    def show_status(self, text: str) -> None:
        self.statuses.append(text)

    def set_speaking(self, speaking: bool) -> None:
        self.speaking = speaking


@dataclass
class FakeAnswers:
    reply: str = "Resposta do Jarvis."
    fail: bool = False
    questions: list[str] = field(default_factory=list)

    def ask(self, question: str) -> str:
        self.questions.append(question)
        if self.fail:
            raise AnswerServiceError("falhou")
        return self.reply

    def interpret_intent(self, utterance: str) -> dict[str, str]:
        if self.fail:
            raise AnswerServiceError("falhou")
        return {"action": "chat", "target": "", "reply": self.reply}


@dataclass
class FakeMessages:
    saved: list[str] = field(default_factory=list)

    def save(self, message: str) -> None:
        self.saved.append(message)


@dataclass
class FakeLauncher:
    launched: list[str] = field(default_factory=list)
    urls: list[str] = field(default_factory=list)
    fail: bool = False

    def launch(self, target: str) -> None:
        if self.fail:
            raise LaunchError(target)
        self.launched.append(target)

    def open_url(self, url: str) -> None:
        if self.fail:
            raise LaunchError(url)
        self.urls.append(url)


@dataclass
class FakeProcessController:
    closed: list[str] = field(default_factory=list)
    running: set[str] = field(default_factory=set)

    def close_app(self, name_or_target: str) -> bool:
        self.closed.append(name_or_target)
        return True

    def list_running(self) -> set[str]:
        return self.running


def make_context(listener_answers: list[str | None] | None = None, **overrides: object) -> CommandContext:
    """Cria um contexto com dublês; qualquer dependência pode ser sobrescrita."""
    deps: dict[str, object] = {
        "speaker": FakeSpeaker(),
        "listener": FakeListener(list(listener_answers or [])),
        "view": FakeView(),
        "answers": FakeAnswers(),
        "messages": FakeMessages(),
        "launcher": FakeLauncher(),
        "processes": FakeProcessController(),
    }
    deps.update(overrides)
    return CommandContext(**deps)  # type: ignore[arg-type]
