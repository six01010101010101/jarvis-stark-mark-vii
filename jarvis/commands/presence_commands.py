"""Comandos de presença, prontidão e saudações em tempo real do J.A.R.V.I.S."""

from __future__ import annotations

from jarvis.commands.registry import Command, CommandContext, Outcome


def _presence_check(ctx: CommandContext, _utterance: str) -> Outcome:
    ctx.reply(
        "Ao seu dispor, senhor Ken. Todos os sistemas estão online, calibrados e à sua inteira disposição.",
    )
    return Outcome.CONTINUE


def _wake_child(ctx: CommandContext, _utterance: str) -> Outcome:
    ctx.reply(
        "Bem-vindo, senhor Ken. Monitor ativo, preferências táticas importadas. Ao seu dispor.",
    )
    return Outcome.CONTINUE


def _greeting_night(ctx: CommandContext, _utterance: str) -> Outcome:
    ctx.reply(
        "Boa noite, senhor Ken. Todos os reatores estão operando com eficiência. O que tem em mente para esta madrugada?",
    )
    return Outcome.CONTINUE


def _greeting_day(ctx: CommandContext, _utterance: str) -> Outcome:
    ctx.reply(
        "Bom dia, senhor Ken. Protocolos ativos e sistemas sincronizados. O que gostaria de executar hoje?",
    )
    return Outcome.CONTINUE


def _greeting_afternoon(ctx: CommandContext, _utterance: str) -> Outcome:
    ctx.reply(
        "Boa tarde, senhor Ken. Às suas ordens. O que tem em mente para agora?",
    )
    return Outcome.CONTINUE


def _status_inquiry(ctx: CommandContext, _utterance: str) -> Outcome:
    ctx.reply(
        "Operando em potência máxima e com excelente humor, senhor Ken. O que gostaria de aprontar hoje?",
    )
    return Outcome.CONTINUE


def presence_commands() -> list[Command]:
    """Retorna comandos de presença, prontidão e saudações imediatas."""
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
            ("como vai", "tudo bem", "como voce esta", "como esta seu dia", "como estao as coisas"),
            _status_inquiry,
        ),
    ]
