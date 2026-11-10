"""Carregamento e validação das configurações do J.A.R.V.I.S. a partir do ambiente/.env."""

from __future__ import annotations

import os
import winreg
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

DEFAULT_GEMINI_MODEL = "gemini-3.5-flash-lite"
DEFAULT_LANGUAGE = "pt-BR"
DEFAULT_WAKE_WORD = "jarvis"
TRANSCRIPTION_FILENAME = "mensagens_salvas.txt"

_SHELL_FOLDERS_KEY = r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"


class ConfigError(Exception):
    """Erro lançado quando uma configuração obrigatória está ausente ou inválida."""


@dataclass(frozen=True)
class Settings:
    """Configurações imutáveis da aplicação."""

    gemini_api_key: str
    gemini_model: str
    user_name: str
    language: str
    wake_word: str
    transcription_file: Path
    supabase_url: str = ""
    supabase_key: str = ""


def resolve_desktop_dir() -> Path:
    """Retorna a Área de Trabalho real do usuário (respeita redirecionamento do OneDrive)."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _SHELL_FOLDERS_KEY) as key:
            raw_value, _ = winreg.QueryValueEx(key, "Desktop")
        return Path(os.path.expandvars(str(raw_value)))
    except OSError:
        return Path.home() / "Desktop"


def _require(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ConfigError(
            f"A variável '{name}' não está definida. Edite o arquivo {ENV_FILE} e preencha-a."
        )
    return value


def load_settings(env_file: Path = ENV_FILE) -> Settings:
    """Lê o arquivo .env (se existir) e as variáveis de ambiente, retornando as configurações.

    Raises:
        ConfigError: se GEMINI_API_KEY ou JARVIS_USER_NAME estiverem ausentes.
    """
    load_dotenv(env_file, override=False)

    transcription_raw = os.getenv("JARVIS_TRANSCRIPTION_FILE", "").strip()
    transcription_file = (
        Path(os.path.expandvars(transcription_raw))
        if transcription_raw
        else resolve_desktop_dir() / TRANSCRIPTION_FILENAME
    )

    return Settings(
        gemini_api_key=_require("GEMINI_API_KEY"),
        gemini_model=os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL).strip() or DEFAULT_GEMINI_MODEL,
        user_name=_require("JARVIS_USER_NAME"),
        language=os.getenv("JARVIS_LANGUAGE", DEFAULT_LANGUAGE).strip() or DEFAULT_LANGUAGE,
        wake_word=(os.getenv("JARVIS_WAKE_WORD", DEFAULT_WAKE_WORD).strip() or DEFAULT_WAKE_WORD).lower(),
        transcription_file=transcription_file,
        supabase_url=os.getenv("SUPABASE_URL", "").strip(),
        supabase_key=os.getenv("SUPABASE_KEY", "").strip(),
    )
