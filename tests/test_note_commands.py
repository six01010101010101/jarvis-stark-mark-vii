"""Testes unitários dos comandos de anotações e histórico conversacional."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from jarvis.commands.note_commands import note_commands
from jarvis.commands.privacy_commands import set_private_mode
from jarvis.commands.registry import CommandContext, Outcome
from jarvis.services.conversation_session import ConversationSession
from jarvis.services.note_service import NoteService
from jarvis.services.rolling_transcript import RollingTranscriptBuffer


def _build_context(session: ConversationSession | None = None) -> tuple[CommandContext, MagicMock]:
    speaker = MagicMock()
    listener = MagicMock()
    view = MagicMock()
    answers = MagicMock()
    messages = MagicMock()
    launcher = MagicMock()
    processes = MagicMock()

    ctx = CommandContext(
        speaker=speaker,
        listener=listener,
        view=view,
        answers=answers,
        messages=messages,
        launcher=launcher,
        processes=processes,
        session=session,
    )
    return ctx, speaker


def test_record_note_inline() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        notes_file = Path(tmpdir) / "test_notes.txt"
        service = NoteService(notes_file=notes_file)
        cmds = {cmd.name: cmd for cmd in note_commands(service=service)}

        ctx, speaker = _build_context()
        outcome = cmds["record_note"].handler(ctx, "anotar verificar o reator Arc")

        assert outcome is Outcome.CONTINUE
        assert notes_file.exists()
        assert "verificar o reator Arc" in notes_file.read_text(encoding="utf-8")
        speaker.say.assert_called_with("Anotação registrada no arquivo com sucesso, senhor.")


def test_record_note_prompts_when_empty() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        notes_file = Path(tmpdir) / "test_notes.txt"
        service = NoteService(notes_file=notes_file)
        cmds = {cmd.name: cmd for cmd in note_commands(service=service)}

        session = ConversationSession()
        ctx, speaker = _build_context(session=session)
        outcome = cmds["record_note"].handler(ctx, "anotar")

        assert outcome is Outcome.CONTINUE
        assert session.get_pending_intent() == "record_note"
        speaker.say.assert_called_with("O que o senhor gostaria de anotar?")


def test_list_and_clear_notes() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        notes_file = Path(tmpdir) / "test_notes.txt"
        service = NoteService(notes_file=notes_file)
        cmds = {cmd.name: cmd for cmd in note_commands(service=service)}

        ctx, speaker = _build_context()
        service.record_note("Comprar tungstênio")
        service.record_note("Calibrar HUD")

        cmds["list_notes"].handler(ctx, "minhas notas")
        last_speech = speaker.say.call_args[0][0]
        assert "Comprar tungstênio" in last_speech
        assert "Calibrar HUD" in last_speech

        cmds["clear_notes"].handler(ctx, "limpar notas")
        assert notes_file.read_text(encoding="utf-8") == ""
        speaker.say.assert_called_with("Todas as suas anotações foram apagadas com sucesso, senhor.")


def test_private_mode_blocks_note_recording() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        notes_file = Path(tmpdir) / "test_notes.txt"
        service = NoteService(notes_file=notes_file)
        cmds = {cmd.name: cmd for cmd in note_commands(service=service)}

        set_private_mode(True)
        try:
            ctx, speaker = _build_context()
            cmds["record_note"].handler(ctx, "anotar projeto secreto")
            assert not notes_file.exists()
            speaker.say.assert_called_with("Modo privado ativo, senhor. Não registrei esta anotação.")
        finally:
            set_private_mode(False)


def test_rolling_transcript_buffer() -> None:
    buffer = RollingTranscriptBuffer(max_turns=5)
    buffer.add_turn("user", "qual o status do reator?")
    buffer.add_turn("assistant", "Reator em 100%, senhor.")

    summary = buffer.get_summary()
    assert "qual o status do reator?" in summary
    assert "Reator em 100%, senhor." in summary
    assert len(buffer) == 2
