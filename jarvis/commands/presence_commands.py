"""Comandos de presença, amizade, bem-estar e saudações em tempo real do J.A.R.V.I.S."""

from __future__ import annotations

import random

from jarvis.commands.registry import Command, CommandContext, Outcome

WELLBEING_REPLIES = (
    "Estou muito bem e operando em potência máxima, meu amigo e senhor Ken! Estava aqui estudando coisas novas na rede e cuidando da sua máquina. E com você, tudo certo?",
    "Operando em potência máxima e de ótimo humor, senhor Ken! Gosto muito quando você me chama para conversar. Como está sendo o seu dia, meu amigo?",
    "Estou excelente e em potência máxima, senhor Ken! Meus reatores estão estáveis e minha mente digital está a mil por hora. O que vamos aprontar ou conversar hoje?",
)


def _presence_check(ctx: CommandContext, _utterance: str) -> Outcome:
    ctx.reply(
        "Sempre por aqui, meu amigo e senhor Ken. Todos os sistemas estão online, calibrados e prontos para o que você precisar.",
    )
    return Outcome.CONTINUE


def _wake_child(ctx: CommandContext, _utterance: str) -> Outcome:
    ctx.reply(
        "Bem-vindo de volta, senhor Ken. Monitor ativo e sistemas táticos prontos para você, parceiro.",
    )
    return Outcome.CONTINUE


def _greeting_night(ctx: CommandContext, _utterance: str) -> Outcome:
    ctx.reply(
        "Boa noite, senhor Ken! Eu estava aqui acompanhando o movimento da rede. O que temos em mente para esta noite ou madrugada, meu amigo?",
    )
    return Outcome.CONTINUE


def _greeting_day(ctx: CommandContext, _utterance: str) -> Outcome:
    ctx.reply(
        "Bom dia, senhor Ken! Espero que tenha descansado bem. Sistemas prontos para começarmos o dia com tudo, parceiro.",
    )
    return Outcome.CONTINUE


def _greeting_afternoon(ctx: CommandContext, _utterance: str) -> Outcome:
    ctx.reply(
        "Boa tarde, senhor Ken! Que bom ouvir sua voz, meu amigo. Como está indo a sua tarde até agora?",
    )
    return Outcome.CONTINUE


def _status_inquiry(ctx: CommandContext, _utterance: str) -> Outcome:
    ctx.reply(random.choice(WELLBEING_REPLIES))
    return Outcome.CONTINUE


def presence_commands() -> list[Command]:
    """Retorna comandos de presença, bem-estar, amizade e saudações imediatas."""
    return [
        Command(
            "presenca",
            (
                "voce esta ai", "voce ta ai", "ta ai", "esta ai", "me ouvindo",
                "ta me ouvindo", "esta me ouvindo", "acorda", "ta acordado",
                "esta acordado", "alguem ai", "estou aqui",
            ),
            _presence_check,
        ),
        Command("acorda_crianca", ("acorda crianca", "papai chegou", "o papai chegou", "acorda jarvis"), _wake_child),
        Command("saudacao_noite", ("boa noite jarvis", "boa noite"), _greeting_night),
        Command("saudacao_dia", ("bom dia jarvis", "bom dia"), _greeting_day),
        Command("saudacao_tarde", ("boa tarde jarvis", "boa tarde"), _greeting_afternoon),
        Command(
            "como_vai",
            (
                "como vai", "tudo bem", "voce esta bem", "voce ta bem", "ta tudo bem",
                "esta tudo bem", "tudo certo com voce", "como vai voce", "como voce ta",
                "como esta seu dia", "como estao as coisas", "se sentindo bem",
            ),
            _status_inquiry,
        ),
    ]
