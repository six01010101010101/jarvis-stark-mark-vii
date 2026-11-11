"""Comandos nativos do Windows para controle de volume, reprodução de mídia e captura de tela."""

from __future__ import annotations

import ctypes

from jarvis.commands.registry import Command, CommandContext, Outcome

VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_PLAY_PAUSE = 0xB3
VK_SNAPSHOT = 0x2C
VK_LWIN = 0x5B
VK_SHIFT = 0x10
KEYEVENTF_KEYUP = 0x0002


def _tap_key(vk_code: int, times: int = 1) -> None:
    user32 = ctypes.windll.user32
    for _ in range(times):
        user32.keybd_event(vk_code, 0, 0, 0)
        user32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP, 0)


def _volume_up(ctx: CommandContext, _utterance: str) -> Outcome:
    _tap_key(VK_VOLUME_UP, times=4)
    ctx.reply("Volume aumentado, senhor.")
    return Outcome.CONTINUE


def _volume_down(ctx: CommandContext, _utterance: str) -> Outcome:
    _tap_key(VK_VOLUME_DOWN, times=4)
    ctx.reply("Volume reduzido, senhor.")
    return Outcome.CONTINUE


def _volume_mute(ctx: CommandContext, _utterance: str) -> Outcome:
    _tap_key(VK_VOLUME_MUTE)
    ctx.reply("Áudio alternado para mudo, senhor.")
    return Outcome.CONTINUE


def _play_pause(ctx: CommandContext, _utterance: str) -> Outcome:
    _tap_key(VK_MEDIA_PLAY_PAUSE)
    ctx.reply("Reprodução de mídia alternada, senhor.")
    return Outcome.CONTINUE


def _next_track(ctx: CommandContext, _utterance: str) -> Outcome:
    _tap_key(VK_MEDIA_NEXT_TRACK)
    ctx.reply("Avançando para a próxima faixa, senhor.")
    return Outcome.CONTINUE


def _prev_track(ctx: CommandContext, _utterance: str) -> Outcome:
    _tap_key(VK_MEDIA_PREV_TRACK)
    ctx.reply("Retornando para a faixa anterior, senhor.")
    return Outcome.CONTINUE


def _screenshot(ctx: CommandContext, _utterance: str) -> Outcome:
    _tap_key(VK_SNAPSHOT)
    ctx.reply("Captura de tela copiada para a área de transferência, senhor.")
    return Outcome.CONTINUE


def multimedia_control_commands() -> list[Command]:
    """Retorna comandos de controle de som e reprodução de mídia."""
    return [
        Command("volume_up", ("aumentar volume", "aumenta o volume", "aumenta o som", "subir o volume", "som mais alto"), _volume_up),
        Command("volume_down", ("diminuir volume", "diminui o volume", "abaixa o som", "abaixar volume", "som mais baixo"), _volume_down),
        Command("volume_mute", ("mutar som", "mutar volume", "mudo", "silenciar som", "tirar som"), _volume_mute),
        Command("media_play_pause", ("pausar musica", "pausar video", "despausar", "continuar musica", "play musica", "pausar midia"), _play_pause),
        Command("media_next", ("proxima musica", "pular musica", "avancar musica", "proxima faixa"), _next_track),
        Command("media_prev", ("musica anterior", "voltar musica", "faixa anterior"), _prev_track),
        Command("screenshot", ("tirar print", "capturar tela", "screenshot", "print screen"), _screenshot),
    ]
