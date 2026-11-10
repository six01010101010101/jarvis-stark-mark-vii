"""Comandos para alternar dinamicamente entre vozes masculinas e femininas."""

from __future__ import annotations

from jarvis.commands.registry import Command, CommandContext, Outcome


def _set_female(ctx: CommandContext, _utterance: str) -> Outcome:
    speaker = ctx.speaker
    if hasattr(speaker, "set_voice"):
        speaker.set_voice("female")
        ctx.reply("Voz alterada para feminina (Maria), senhor.")
    else:
        ctx.reply("O sintetizador atual não suporta troca dinâmica de voz, senhor.")
    return Outcome.CONTINUE


def _set_male(ctx: CommandContext, _utterance: str) -> Outcome:
    speaker = ctx.speaker
    if hasattr(speaker, "set_voice"):
        speaker.set_voice("male")
        ctx.reply("Voz alterada para masculina (Daniel), senhor.")
    else:
        ctx.reply("O sintetizador atual não suporta troca dinâmica de voz, senhor.")
    return Outcome.CONTINUE


def _voice_status(ctx: CommandContext, _utterance: str) -> Outcome:
    speaker = ctx.speaker
    current = getattr(speaker, "get_voice", lambda: "padrão")()
    ctx.reply(f"O perfil de voz em operação no momento é {current}, senhor.")
    return Outcome.CONTINUE


def voice_commands() -> tuple[Command, ...]:
    """Retorna comandos de controle e seleção de vozes do assistente."""
    return (
        Command("voice_female", ("voz feminina", "mudar voz para feminina", "trocar voz para feminina", "usar voz da maria", "voz de mulher"), _set_female),
        Command("voice_male", ("voz masculina", "mudar voz para masculina", "trocar voz para masculina", "usar voz do daniel", "voz de homem"), _set_male),
        Command("voice_status", ("qual voz", "qual e a voz", "voz atual"), _voice_status),
    )
