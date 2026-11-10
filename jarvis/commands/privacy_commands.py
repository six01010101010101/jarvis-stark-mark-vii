"""Comandos para ativação e desativação do Modo Privado (sem registro em banco)."""

from __future__ import annotations

from jarvis.commands.registry import Command, CommandContext, Outcome

_private_mode: bool = False


def is_private_mode() -> bool:
    """Retorna se o modo confidencial/privado está atualmente ativo."""
    return _private_mode


def set_private_mode(enabled: bool) -> None:
    """Altera o estado do modo privado."""
    global _private_mode
    _private_mode = enabled


def _enable_private(ctx: CommandContext, _utterance: str) -> Outcome:
    set_private_mode(True)
    ctx.reply("Modo privado ativado, senhor. Não registrarei histórico de conversas nem anotações.")
    return Outcome.CONTINUE


def _disable_private(ctx: CommandContext, _utterance: str) -> Outcome:
    set_private_mode(False)
    ctx.reply("Modo privado desativado, senhor. Retornando ao registro padrão de dados.")
    return Outcome.CONTINUE


def privacy_commands() -> list[Command]:
    """Retorna comandos de controle de privacidade e modo anônimo."""
    return [
        Command("enable_private_mode", ("ativar modo privado", "modo privado", "modo anonimo", "modo confidencial"), _enable_private),
        Command("disable_private_mode", ("desativar modo privado", "sair do modo privado", "desativar anonimo"), _disable_private),
    ]
