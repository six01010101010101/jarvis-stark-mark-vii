"""Contratos (abstrações) usados pelo assistente, permitindo trocar implementações e testar isoladamente."""

from __future__ import annotations

from typing import Protocol


class AnswerServiceError(Exception):
    """Falha ao obter resposta do serviço de IA."""


class LaunchError(Exception):
    """Falha ao abrir um programa, URI ou URL."""


class Speaker(Protocol):
    """Sintetiza texto em fala e permite alternância dinâmica de vozes."""

    def say(self, text: str) -> None:
        """Fala o texto e bloqueia até terminar."""
        ...

    def stop(self) -> None:
        """Interrompe a fala imediatamente."""
        ...

    def set_voice(self, profile: str) -> bool:
        """Alterna a voz ativa (ex: 'male' / 'female')."""
        ...

    def get_voice(self) -> str:
        """Retorna o nome ou perfil da voz em uso."""
        ...



class Listener(Protocol):
    """Captura e reconhece a fala do usuário."""

    def listen(self) -> str | None:
        """Escuta o microfone e retorna o texto reconhecido, ou None se não entendeu."""
        ...


class StatusView(Protocol):
    """Exibe o estado do assistente na interface."""

    def show_status(self, text: str) -> None:
        """Atualiza o texto de status."""
        ...

    def set_speaking(self, speaking: bool) -> None:
        """Indica se o assistente está falando (ativa/desativa a animação)."""
        ...


class WakeSignal(Protocol):
    """Indicador visual de ativação por voz (LED verde ao ouvir 'Jarvis')."""

    def set_wake_state(self, state: str, heard: str = "") -> None:
        """Atualiza o indicador: 'standby', 'heard' ou 'dialogue'."""
        ...


class AnswerProvider(Protocol):
    """Responde perguntas em linguagem natural e interpreta intenções com IA."""

    def ask(self, question: str) -> str:
        """Retorna a resposta para a pergunta."""
        ...

    def interpret_intent(self, utterance: str) -> dict[str, str]:
        """Classifica intenções com correção inteligente de pronúncia e digitação."""
        ...


class MessageStore(Protocol):
    """Persiste mensagens transcritas."""

    def save(self, message: str) -> None:
        """Grava a mensagem com data/hora."""
        ...


class ProgramLauncher(Protocol):
    """Abre programas, URIs e URLs no sistema operacional."""

    def launch(self, target: str) -> None:
        """Abre o programa/URI indicado (equivalente ao comando 'start' do Windows)."""
        ...

    def open_url(self, url: str) -> None:
        """Abre uma URL no navegador padrão."""
        ...


class ProcessController(Protocol):
    """Gerencia e fecha processos em execução no Windows em tempo real."""

    def close_app(self, name_or_target: str) -> bool:
        """Encerra um aplicativo pelo nome, executável ou variação."""
        ...

    def list_running(self) -> set[str]:
        """Retorna os nomes dos executáveis em execução."""
        ...


class CognitiveService(Protocol):
    """Gera artefatos cognitivos e de aprendizagem (mapas mentais, notas, flashcards, resumos)."""

    def generate_mind_map(self, topic: str) -> str:
        ...

    def generate_sticky_notes(self, topic: str) -> str:
        ...

    def generate_visual_learning(self, topic: str) -> str:
        ...

    def explain_three_levels(self, topic: str) -> str:
        ...

    def generate_flashcards(self, topic: str) -> str:
        ...

    def generate_quiz(self, topic: str) -> str:
        ...

    def generate_study_roadmap(self, topic: str, period: str = "4 semanas") -> str:
        ...

