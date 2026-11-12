"""Módulo de cibersegurança e higienização defensiva do J.A.R.V.I.S."""

from __future__ import annotations

from pathlib import Path
import re

DANGEROUS_SHELL_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"[;&|`$><]"),
    re.compile(r"\$\([^\)]*\)"),
    re.compile(r"\b(?:powershell|cmd|bash|sh|exec|system|popen)\b", re.IGNORECASE),
)

SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"AIza[0-9A-Za-z\-_]{35}"),
    re.compile(r"sk-[a-zA-Z0-9]{20,}"),
    re.compile(r"Bearer\s+[a-zA-Z0-9_\-\.]+", re.IGNORECASE),
    re.compile(r"(?:api[_-]?key|secret|password|token)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-\.]{8,})['\"]?", re.IGNORECASE),
)


class SecurityGuard:
    """Guarda defensivo contra injeção de comandos, travessia de pastas e vazamento de chaves."""

    @staticmethod
    def sanitize_command_argument(arg: str) -> str:
        """Limpa argumentos de entrada removendo caracteres perigosos de interpolação shell."""
        if not arg:
            return ""
        cleaned = re.sub(r"[;&|`$><\"'()\n\r]", "", arg)
        return cleaned.strip()

    @staticmethod
    def is_safe_shell_input(text: str) -> bool:
        """Valida se uma instrução de texto não contém vetores óbvios de exploração de shell."""
        if not text:
            return True
        for pattern in DANGEROUS_SHELL_PATTERNS:
            if pattern.search(text):
                return False
        return True

    @staticmethod
    def is_safe_path(target_path: str | Path, base_dir: Path | None = None) -> bool:
        """Verifica se o caminho fornecido não possui path traversal (..) ou foge da raiz segura."""
        raw_str = str(target_path)
        if ".." in raw_str or "\x00" in raw_str:
            return False
        try:
            resolved = Path(target_path).resolve()
            if base_dir:
                return resolved.is_relative_to(base_dir.resolve())
            return True
        except Exception:
            return False

    @staticmethod
    def redact_secrets(text: str) -> str:
        """Oculta tokens de API, senhas e credenciais confidenciais de logs e do sintetizador de voz."""
        if not text:
            return ""
        sanitized = text
        for pattern in SECRET_PATTERNS:
            sanitized = pattern.sub("[REDACTED_CREDENTIAL]", sanitized)
        return sanitized

    @staticmethod
    def validate_chat_input(text: str, max_length: int = 4096) -> tuple[bool, str]:
        """Garante tamanho razoável e ausência de caracteres nulos ou ataques de buffer."""
        if not text:
            return False, "Mensagem vazia."
        if len(text) > max_length:
            return False, f"Tamanho excede o limite permitido de {max_length} caracteres."
        if "\x00" in text:
            return False, "Caractere nulo não permitido."
        return True, "OK"
