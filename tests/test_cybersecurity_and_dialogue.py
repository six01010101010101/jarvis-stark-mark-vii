"""Testes de Cibersegurança (SecurityGuard, APIShield) e Inteligência Conversacional tipo Gemini."""

from __future__ import annotations

import json
from pathlib import Path
import time
import urllib.request
import urllib.error

from jarvis.database.connection import DatabaseConnection
from jarvis.database.migrations import run_migrations
from jarvis.repositories.memory_repository import MemoryRepository
from jarvis.security.api_shield import APIShield
from jarvis.security.security_guard import SecurityGuard
from jarvis.services.collective_mind import JarvisCollectiveMind
from jarvis.services.conversational_engine import ConversationalEngine
from jarvis.services.jarvis_api_server import JarvisLiveAPIServer
from jarvis.services.local_brain import LocalStarkBrain


def test_security_guard_shell_and_path() -> None:
    # 1. Higienização de argumentos shell
    assert SecurityGuard.sanitize_command_argument("calc.exe & dir") == "calc.exe  dir"
    assert SecurityGuard.sanitize_command_argument("notepad; whoami") == "notepad whoami"
    assert SecurityGuard.sanitize_command_argument("$(reboot)") == "reboot"

    # 2. Detecção de shell perigoso
    assert SecurityGuard.is_safe_shell_input("calc.exe") is True
    assert SecurityGuard.is_safe_shell_input("calc.exe | dir") is False
    assert SecurityGuard.is_safe_shell_input("notepad; cmd.exe") is False
    assert SecurityGuard.is_safe_shell_input("powershell -enc AAAA") is False

    # 3. Path Traversal
    assert SecurityGuard.is_safe_path("docs/relatorio.pdf") is True
    assert SecurityGuard.is_safe_path("../../windows/system32") is False
    assert SecurityGuard.is_safe_path("pasta/../secreto.txt") is False


def test_security_guard_secret_redaction_and_validation() -> None:
    # 1. Ocultação de credenciais
    leaked = "Minha chave é AIzaSyD12345678901234567890123456789012 e token sk-123456789012345678901234"
    redacted = SecurityGuard.redact_secrets(leaked)
    assert "AIza" not in redacted
    assert "sk-" not in redacted
    assert "[REDACTED_CREDENTIAL]" in redacted

    # 2. Validação de mensagens
    ok_valid, _ = SecurityGuard.validate_chat_input("Olá Jarvis")
    assert ok_valid is True
    empty_valid, _ = SecurityGuard.validate_chat_input("")
    assert empty_valid is False
    null_valid, _ = SecurityGuard.validate_chat_input("ataque\x00nulo")
    assert null_valid is False
    big_valid, _ = SecurityGuard.validate_chat_input("a" * 5000, max_length=100)
    assert big_valid is False


def test_api_shield_rate_limit_and_headers() -> None:
    shield = APIShield(max_requests=3, window_seconds=1.0)
    ip = "192.168.1.100"
    assert shield.is_rate_limited(ip) is False
    assert shield.is_rate_limited(ip) is False
    assert shield.is_rate_limited(ip) is False
    assert shield.is_rate_limited(ip) is True  # 4ª requisição bloqueada

    headers = shield.get_security_headers()
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"
    assert "Content-Security-Policy" in headers

    assert shield.validate_payload_size(1024) is True
    assert shield.validate_payload_size(100_000) is False


def test_conversational_engine_and_interrogative_protection() -> None:
    # 1. Distinção entre pergunta e comando
    assert ConversationalEngine.is_interrogative_or_conversational("o que e o discord") is True
    assert ConversationalEngine.is_interrogative_or_conversational("como funciona o chrome") is True
    assert ConversationalEngine.is_interrogative_or_conversational("me explica sobre gravidade") is True
    assert ConversationalEngine.is_interrogative_or_conversational("me da uma dica") is True
    assert ConversationalEngine.is_interrogative_or_conversational("abrir discord") is False
    assert ConversationalEngine.is_interrogative_or_conversational("iniciar google chrome") is False

    # 2. Respostas humanizadas tipo Gemini
    engine = ConversationalEngine()
    reply_well = engine.generate_reply("você está bem?")
    assert "bem" in reply_well.lower()
    assert len(reply_well) > 20

    reply_tip = engine.generate_reply("me dá uma dica")
    assert "dica" in reply_tip.lower() or "foco" in reply_tip.lower()

    reply_explain = engine.generate_reply("o que é inteligência artificial?")
    assert "inteligência artificial" in reply_explain.lower() or "inteligencia artificial" in reply_explain.lower()


def test_local_stark_brain_does_not_open_apps_on_questions() -> None:
    # Ao perguntar sobre um app, NÃO deve abrir o app! Deve responder conversacionalmente
    res_discord_q = LocalStarkBrain.resolve_intent("o que é o discord?")
    assert res_discord_q["action"] == "chat"
    assert res_discord_q.get("target", "") == ""

    res_yt_q = LocalStarkBrain.resolve_intent("como funciona o youtube?")
    assert res_yt_q["action"] == "chat"
    assert res_yt_q.get("target", "") == ""

    # Já comandos imperativos continuam abrindo normalmente
    res_open = LocalStarkBrain.resolve_intent("abrir discord")
    assert res_open["action"] == "open_app"
    assert res_open["target"] == "discord"


def test_live_api_server_shielded_headers(tmp_path: Path) -> None:
    db = DatabaseConnection(str(tmp_path / "test_api_shield.db"))
    run_migrations(db.get_connection())
    repo = MemoryRepository(db)
    mind = JarvisCollectiveMind(repo=repo)

    server = JarvisLiveAPIServer(mind=mind, host="127.0.0.1", port=8771)
    server.start_in_background()
    time.sleep(0.3)

    try:
        req = urllib.request.Request("http://127.0.0.1:8771/api/v1/status")
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            headers = dict(resp.headers)
            assert headers.get("X-Content-Type-Options") == "nosniff"
            assert headers.get("X-Frame-Options") == "DENY"
            assert "Content-Security-Policy" in headers
    finally:
        server.stop()
