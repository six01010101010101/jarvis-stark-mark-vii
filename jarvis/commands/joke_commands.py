"""Comandos de humor e piadas genuínas com encerramento imediato do diálogo."""

from __future__ import annotations

import random
from jarvis.commands.registry import Command, CommandContext, Outcome

TECH_JOKES: tuple[str, ...] = (
    "Por que o programador foi ao médico? Porque ele estava com dor nas costas... de tanto carregar o projeto nas costas!",
    "Existem 10 tipos de pessoas no mundo: as que entendem binário e as que não entendem.",
    "O que o objeto disse para a classe? 'Você não tem métodos para me controlar!'",
    "Por que o computador foi preso? Porque ele executou um processo suspeito!",
    "Qual é o café preferido do desenvolvedor? O Java, é claro!",
    "Um SQL entra num bar, vai até duas mesas e pergunta: 'Posso dar um JOIN em vocês?'",
    "Sabe qual é a diferença entre um bug e uma feature? A feature vem documentada, senhor!",
    "Por que o livro de matemática se suicidou? Porque ele tinha muitos problemas.",
    "O que o roteador falou para o computador? 'Calma aí, vamos manter uma boa conexão entre a gente.'",
    "Por que o desenvolvedor não gosta de natureza? Porque tem muito bug solto por lá!",
)


def _tell_joke_handler(ctx: CommandContext, _utterance: str) -> Outcome:
    """Conta uma piada divertida e encerra o ciclo de conversa imediatamente."""
    joke = random.choice(TECH_JOKES)
    ctx.reply(f"Aqui vai uma para descontrair: {joke}")
    if ctx.session and hasattr(ctx.session, "close_dialogue"):
        ctx.session.close_dialogue()
    return Outcome.CONTINUE


def joke_commands() -> tuple[Command, ...]:
    """Retorna comandos de piadas do Jarvis."""
    return (
        Command(
            name="tell_funny_joke",
            triggers=(
                "conte uma piada", "me conte uma piada", "me conta uma piada",
                "faz uma piada", "fale uma piada", "diga uma piada",
                "manda uma piada", "outra piada", "conta piada",
            ),
            handler=_tell_joke_handler,
        ),
    )
