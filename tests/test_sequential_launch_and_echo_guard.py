"""Testes unitários para execução sequencial (fala antes de abrir) e proteção de microfone contra soundbar."""

from __future__ import annotations

import time
from unittest.mock import MagicMock

from jarvis.commands import build_registry
from jarvis.speech.listener import GoogleSpeechListener
from jarvis.speech.vad_recorder import AdaptiveVadRecorder
from tests.fakes import make_context


def test_sequential_app_launch_speaks_before_opening() -> None:
    order: list[str] = []
    ctx = make_context()

    orig_say = ctx.speaker.say
    orig_launch = ctx.launcher.launch

    def tracking_say(text: str) -> None:
        order.append(f"say:{text}")
        orig_say(text)

    def tracking_launch(target: str) -> None:
        order.append(f"launch:{target}")
        orig_launch(target)

    ctx.speaker.say = tracking_say  # type: ignore[assignment]
    ctx.launcher.launch = tracking_launch  # type: ignore[assignment]

    build_registry().dispatch(ctx, "abrir calculadora")

    assert len(order) >= 2
    assert order[0].startswith("say:Entendido, senhor. Abrindo")
    assert order[1] == "launch:calc.exe"


def test_sequential_url_launch_speaks_before_opening() -> None:
    order: list[str] = []
    ctx = make_context()

    orig_say = ctx.speaker.say
    orig_url = ctx.launcher.open_url

    def tracking_say(text: str) -> None:
        order.append(f"say:{text}")
        orig_say(text)

    def tracking_url(url: str) -> None:
        order.append(f"url:{url}")
        orig_url(url)

    ctx.speaker.say = tracking_say  # type: ignore[assignment]
    ctx.launcher.open_url = tracking_url  # type: ignore[assignment]

    build_registry().dispatch(ctx, "abrir youtube")

    assert len(order) >= 2
    assert order[0].startswith("say:Colocando no YouTube")
    assert order[1] == "url:https://www.youtube.com"


def test_vad_recorder_echo_guard_discards_during_and_after_speech() -> None:
    vad = AdaptiveVadRecorder()
    mock_stream = MagicMock()
    mock_stream.read.return_value = b"\x80\x05" * 512

    # Durante fala (is_speaking() == True), não deve iniciar captura
    is_speaking = MagicMock(return_value=True)
    stop_event = MagicMock()
    stop_event.is_set.side_effect = [False, False, True]

    audio, typed, dur, peak = vad.record_phrase(
        stream=mock_stream,
        sample_rate=16000,
        sample_width=2,
        chunk_size=1024,
        is_speaking=is_speaking,
        stop_event=stop_event,
    )

    assert audio is None
    assert vad._echo_guard_until > time.monotonic()


def test_listener_clears_queue_on_capture() -> None:
    listener = GoogleSpeechListener(language="pt-BR")
    assert not listener._listening.is_set()
    listener._phrase_queue.put((None, "teste digitado", 0.0, 0))
    res = listener.listen(idle_timeout=0.2)
    assert res == "teste digitado"
    assert not listener._listening.is_set()
    assert listener._phrase_queue.empty()
    listener.close()
