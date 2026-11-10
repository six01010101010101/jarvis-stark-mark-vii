"""Comandos de voz para inspeção e captura da tela do computador."""

from __future__ import annotations

from jarvis.commands.registry import Command, CommandContext, Outcome
from jarvis.services.screen_inspector import ScreenInspector

_DEFAULT_INSPECTOR = ScreenInspector()


def _inspect_screen(ctx: CommandContext, _utterance: str, inspector: ScreenInspector = _DEFAULT_INSPECTOR) -> Outcome:
    info = inspector.inspect(take_screenshot=False)
    msg = f"Senhor Ken, {info.describe()}"
    ctx.reply(msg)
    return Outcome.CONTINUE


def _capture_screen(ctx: CommandContext, _utterance: str, inspector: ScreenInspector = _DEFAULT_INSPECTOR) -> Outcome:
    info = inspector.inspect(take_screenshot=True)
    if info.screenshot_path and info.screenshot_path.exists():
        msg = f"Captura de tela realizada com sucesso, senhor. Salva como {info.screenshot_path.name}."
    else:
        msg = "Ferramenta de captura de tela acionada na área de trabalho, senhor."
    ctx.reply(msg)
    return Outcome.CONTINUE


def screen_commands(inspector: ScreenInspector | None = None) -> list[Command]:
    """Retorna os comandos de inspeção e captura visual de tela."""
    active_inspector = inspector or _DEFAULT_INSPECTOR
    return [
        Command(
            "screen_inspect",
            (
                "o que tem na minha tela",
                "o que esta na minha tela",
                "o que está na minha tela",
                "analisar tela",
                "inspecionar tela",
                "ver tela",
                "janela ativa",
            ),
            lambda ctx, utt: _inspect_screen(ctx, utt, active_inspector),
        ),
        Command(
            "screen_capture",
            (
                "tirar print",
                "capturar tela",
                "screenshot",
                "tirar foto da tela",
                "print screen",
                "salvar tela",
            ),
            lambda ctx, utt: _capture_screen(ctx, utt, active_inspector),
        ),
    ]
