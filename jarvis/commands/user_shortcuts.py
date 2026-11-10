"""Comandos para acesso rápido aos perfis pessoais de Ken (Instagram, YouTube, WhatsApp)."""

from __future__ import annotations

import ctypes
import re

from jarvis.commands.registry import Command, CommandContext, Outcome
from jarvis.services.user_profile import KEN_PROFILE

VK_CONTROL = 0x11
VK_BACK = 0x08
KEYEVENTF_KEYUP = 0x0002


def _send_clear_keys() -> None:
    user32 = ctypes.windll.user32
    # Ctrl + A
    user32.keybd_event(VK_CONTROL, 0, 0, 0)
    user32.keybd_event(0x41, 0, 0, 0)  # 'A'
    user32.keybd_event(0x41, 0, KEYEVENTF_KEYUP, 0)
    user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
    # Backspace
    user32.keybd_event(VK_BACK, 0, 0, 0)
    user32.keybd_event(VK_BACK, 0, KEYEVENTF_KEYUP, 0)


def _open_instagram(ctx: CommandContext, _utterance: str) -> Outcome:
    ctx.launcher.open_url(KEN_PROFILE.get_instagram_url())
    ctx.reply(f"Acessando seu perfil no Instagram @{KEN_PROFILE.instagram_handle}, senhor.")
    return Outcome.CONTINUE


def _open_youtube(ctx: CommandContext, _utterance: str) -> Outcome:
    ctx.launcher.open_url(KEN_PROFILE.get_youtube_url())
    ctx.reply(f"Abrindo o YouTube na conta {KEN_PROFILE.youtube_email}, senhor.")
    return Outcome.CONTINUE


def _open_whatsapp(ctx: CommandContext, utterance: str) -> Outcome:
    match = re.search(r"(?:dizendo|com a mensagem|falando)\s+(.+)$", utterance, re.I)
    msg = match.group(1).strip() if match else ""
    ctx.launcher.open_url(KEN_PROFILE.get_whatsapp_url(msg))
    ctx.reply(f"Abrindo WhatsApp no seu número {KEN_PROFILE.whatsapp_number}, senhor.")
    return Outcome.CONTINUE


def _clear_text(ctx: CommandContext, _utterance: str) -> Outcome:
    _send_clear_keys()
    ctx.reply("Texto e mensagem apagados do campo de edição, senhor.")
    return Outcome.CONTINUE


def user_shortcuts() -> list[Command]:
    """Retorna comandos de acesso rápido às contas pessoais de Ken."""
    return [
        Command("my_instagram", ("abrir meu instagram", "meu instagram", "meu insta", "dracos6x", "meu feed"), _open_instagram),
        Command("my_youtube", ("abrir meu youtube", "meu youtube", "minha conta do youtube", "youtube do ken"), _open_youtube),
        Command("my_whatsapp", ("abrir meu whatsapp", "meu whatsapp", "meu zap", "meu numero", "mensagem para mim"), _open_whatsapp),
        Command("clear_text", ("apagar mensagem", "apagar tudo", "limpar texto", "apagar texto", "limpar mensagem"), _clear_text),
    ]
