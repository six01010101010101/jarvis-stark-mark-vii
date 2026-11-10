"""Serviço de gerenciamento de anotações por voz inspirado no Projeto J.A.R.V.I.S."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from jarvis.commands.privacy_commands import is_private_mode

logger = logging.getLogger(__name__)

DEFAULT_NOTES_PATH = Path(__file__).resolve().parent.parent.parent / "notas_jarvis.txt"


class NoteService:
    """Registra e recupera anotações ditadas pelo usuário."""

    def __init__(self, notes_file: Path = DEFAULT_NOTES_PATH) -> None:
        self._notes_file = notes_file

    def record_note(self, content: str) -> str:
        """Salva uma nova anotação com data e hora no arquivo de notas."""
        if is_private_mode():
            return "Modo privado ativo, senhor. Não registrei esta anotação."

        clean = content.strip()
        if not clean:
            return "Não identifiquei o conteúdo da nota para registrar, senhor."

        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
        entry = f"[{timestamp}] {clean}\n"
        try:
            with open(self._notes_file, "a", encoding="utf-8") as f:
                f.write(entry)
            logger.info("Anotação registrada: %s", clean)
            return "Anotação registrada no arquivo com sucesso, senhor."
        except OSError as exc:
            logger.error("Falha ao salvar nota: %s", exc)
            return "Houve uma falha ao gravar a anotação no disco, senhor."

    def list_notes(self, max_entries: int = 4) -> str:
        """Lê as anotações mais recentes registradas."""
        if not self._notes_file.exists():
            return "O senhor ainda não possui nenhuma anotação gravada."

        try:
            lines = self._notes_file.read_text(encoding="utf-8").strip().splitlines()
            if not lines:
                return "Seu bloco de anotações está vazio no momento, senhor."

            recent = lines[-max_entries:]
            return f"Senhor Ken, aqui estão suas últimas notas:\n" + "\n".join(recent)
        except OSError as exc:
            logger.error("Falha ao ler notas: %s", exc)
            return "Não foi possível acessar seu arquivo de notas agora, senhor."

    def clear_notes(self) -> str:
        """Limpa todo o arquivo de anotações."""
        try:
            if self._notes_file.exists():
                self._notes_file.write_text("", encoding="utf-8")
            return "Todas as suas anotações foram apagadas com sucesso, senhor."
        except OSError as exc:
            logger.error("Falha ao limpar notas: %s", exc)
            return "Não foi possível limpar o arquivo de anotações, senhor."
