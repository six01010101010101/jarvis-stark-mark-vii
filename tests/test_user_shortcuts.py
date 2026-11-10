"""Testes dos atalhos pessoais do senhor Ken (YouTube, Instagram, WhatsApp, Apagar)."""

from __future__ import annotations

from jarvis.commands import Outcome, build_registry
from jarvis.services.user_profile import KEN_PROFILE, UserProfile
from tests.fakes import make_context


def test_user_profile_values() -> None:
    assert KEN_PROFILE.name == "Ken Kobayashi"
    assert KEN_PROFILE.youtube_email == "keekobayashi2005@gmail.com"
    assert KEN_PROFILE.google_email == "kenkobayashi2005@gmail.com"
    assert KEN_PROFILE.whatsapp_number == "5511981237033"
    assert KEN_PROFILE.instagram_handle == "dracos6x"
    assert KEN_PROFILE.get_instagram_url() == "https://www.instagram.com/dracos6x/"
    assert KEN_PROFILE.get_youtube_url() == "https://www.youtube.com/"
    assert "5511981237033" in KEN_PROFILE.get_whatsapp_url()
    assert "ola" in KEN_PROFILE.get_whatsapp_url("ola")


def test_open_my_instagram_shortcut() -> None:
    ctx = make_context()
    registry = build_registry()

    outcome = registry.dispatch(ctx, "abrir meu instagram")
    assert outcome is Outcome.CONTINUE
    assert "https://www.instagram.com/dracos6x/" in ctx.launcher.urls  # type: ignore[attr-defined]
    spoken = ctx.speaker.spoken[-1]  # type: ignore[attr-defined]
    assert "dracos6x" in spoken


def test_open_my_youtube_shortcut() -> None:
    ctx = make_context()
    registry = build_registry()

    outcome = registry.dispatch(ctx, "abrir meu youtube")
    assert outcome is Outcome.CONTINUE
    assert "https://www.youtube.com/" in ctx.launcher.urls  # type: ignore[attr-defined]
    spoken = ctx.speaker.spoken[-1]  # type: ignore[attr-defined]
    assert "keekobayashi2005@gmail.com" in spoken


def test_open_my_whatsapp_with_and_without_message() -> None:
    ctx = make_context()
    registry = build_registry()

    outcome1 = registry.dispatch(ctx, "abrir meu whatsapp")
    assert outcome1 is Outcome.CONTINUE
    assert any("5511981237033" in url for url in ctx.launcher.urls)  # type: ignore[attr-defined]

    outcome2 = registry.dispatch(ctx, "meu whatsapp dizendo estou a caminho")
    assert outcome2 is Outcome.CONTINUE
    assert any("estou%20a%20caminho" in url for url in ctx.launcher.urls)  # type: ignore[attr-defined]


def test_clear_text_command_dispatches() -> None:
    ctx = make_context()
    registry = build_registry()

    outcome = registry.dispatch(ctx, "apagar mensagem")
    assert outcome is Outcome.CONTINUE
    spoken = ctx.speaker.spoken[-1]  # type: ignore[attr-defined]
    assert "apagados" in spoken
