"""Automação do Windows Explorer, navegação de diretórios e seleção de arquivos."""

from __future__ import annotations

import logging
import os
from pathlib import Path
import subprocess

from jarvis.security.security_guard import SecurityGuard

logger = logging.getLogger(__name__)

SPECIAL_FOLDERS: dict[str, Path] = {
    "downloads": Path.home() / "Downloads",
    "documentos": Path.home() / "Documents",
    "documents": Path.home() / "Documents",
    "desktop": Path.home() / "Desktop",
    "area de trabalho": Path.home() / "Desktop",
    "área de trabalho": Path.home() / "Desktop",
    "imagens": Path.home() / "Pictures",
    "pictures": Path.home() / "Pictures",
    "videos": Path.home() / "Videos",
    "vídeos": Path.home() / "Videos",
    "musica": Path.home() / "Music",
    "música": Path.home() / "Music",
    "c": Path("C:\\"),
    "disco local": Path("C:\\"),
}


class WindowsExplorerAutomation:
    """Controlador de alto nível para o Windows Explorer e sistema de arquivos."""

    def open_folder(self, target: str | Path = "") -> bool:
        """Abre o Windows Explorer na pasta indicada ou no diretório de Downloads/Desktop."""
        if not SecurityGuard.is_safe_shell_input(str(target)):
            logger.warning("Tentativa de injeção bloqueada em open_folder: %s", target)
            return False
        folder_path = self._resolve_path(target)
        try:
            target_str = str(folder_path) if folder_path.exists() else str(Path.home())
            subprocess.Popen(["explorer.exe", target_str], shell=False)
            logger.info("Windows Explorer aberto em: %s", target_str)
            return True
        except Exception as exc:
            logger.error("Falha ao abrir Explorer: %s", exc)
            return False

    def select_file_in_explorer(self, file_path: str | Path) -> bool:
        """Abre o Explorer destacando/selecionando visualmente o arquivo solicitado."""
        if not SecurityGuard.is_safe_shell_input(str(file_path)):
            logger.warning("Tentativa de injeção bloqueada em select_file: %s", file_path)
            return False
        resolved = Path(file_path).expanduser().resolve()
        if not resolved.exists():
            found = self.search_user_file(str(file_path))
            if found:
                resolved = found
            else:
                logger.warning("Arquivo não encontrado para seleção: %s", file_path)
                return False
        try:
            # Comando nativo do Windows: explorer.exe /select,"C:\caminho\arquivo.ext"
            subprocess.Popen(["explorer.exe", f"/select,{resolved}"], shell=False)
            logger.info("Arquivo selecionado no Explorer: %s", resolved)
            return True
        except Exception as exc:
            logger.error("Falha ao selecionar arquivo no Explorer: %s", exc)
            return False

    def search_user_file(self, query: str) -> Path | None:
        """Localiza rapidamente um arquivo pelo nome nas pastas principais do usuário."""
        q_clean = query.strip().lower()
        search_roots = [
            Path.home() / "Downloads",
            Path.home() / "Documents",
            Path.home() / "Desktop",
        ]
        for root in search_roots:
            if not root.exists():
                continue
            try:
                for entry in root.iterdir():
                    if entry.is_file() and q_clean in entry.name.lower():
                        return entry
            except Exception:
                continue
        return None

    def _resolve_path(self, target: str | Path) -> Path:
        """Resolve apelidos populares de pastas ou caminhos no sistema."""
        if isinstance(target, Path):
            return target
        clean = target.strip().lower()
        if not clean:
            return Path.home()
        if clean in SPECIAL_FOLDERS:
            return SPECIAL_FOLDERS[clean]
        p = Path(target).expanduser().resolve()
        return p if p.exists() else Path.home()
