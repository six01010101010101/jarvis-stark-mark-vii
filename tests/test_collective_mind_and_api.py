"""Testes unitários da Mente Coletiva, Distinção Semântica, Banco Episódico e Servidor API."""

from __future__ import annotations

import json
from pathlib import Path
import threading
import time
import urllib.request

from jarvis.database.connection import DatabaseConnection
from jarvis.database.migrations import run_migrations
from jarvis.repositories.memory_repository import MemoryRepository
from jarvis.services.collective_mind import JarvisCollectiveMind
from jarvis.services.jarvis_api_server import JarvisLiveAPIServer
from jarvis.services.semantic_wake_analyzer import SemanticWakeAnalyzer
from jarvis.text_utils import extract_wake_and_command


def test_semantic_distinction_between_wake_and_subject() -> None:
    # 1. "Jarvis, o que seria o Jarvis?" deve preservar o sujeito da pergunta
    is_wake, cmd = extract_wake_and_command("Jarvis, o que seria o Jarvis?")
    assert is_wake is True
    assert "jarvis" in cmd.lower()
    assert "o que seria" in cmd.lower()

    # 2. "Quem é o Jarvis?" não deve cortar o nome Jarvis
    is_wake_q, cmd_q = extract_wake_and_command("Quem é o Jarvis?")
    assert is_wake_q is True
    assert "quem" in cmd_q.lower()
    assert "jarvis" in cmd_q.lower()

    # 3. Chamada pura ("Jarvis" ou "Oi Jarvis") deve retornar comando vazio
    is_wake_pure, cmd_pure = extract_wake_and_command("Jarvis")
    assert is_wake_pure is True
    assert cmd_pure == ""

    is_wake_hi, cmd_hi = extract_wake_and_command("Oi Jarvis")
    assert is_wake_hi is True
    assert cmd_hi == ""


def test_episodic_database_and_facts_learning(tmp_path: Path) -> None:
    db_file = tmp_path / "test_episodic.db"
    db = DatabaseConnection(str(db_file))
    run_migrations(db.get_connection())
    repo = MemoryRepository(db)

    # Verifica fato de auto-consciência inicial
    facts = repo.get_learned_facts()
    assert any("Jarvis Stark Mark VII" in f for f in facts)

    # Extrai novos fatos sobre o usuário
    repo._extract_user_facts("Meu projeto atual é desenvolver um drone inteligente", "2026-11-11T00:00:00")
    updated_facts = repo.get_learned_facts()
    assert any("drone inteligente" in f for f in updated_facts)

    # Grava e recupera histórico episódico
    repo.save_episodic_turn("O que você acha da arquitetura?", "Acho excelente, senhor.", lang="pt")
    history = repo.get_recent_episodic_context(limit=5)
    assert len(history) >= 2
    assert history[-2]["role"] == "user"
    assert history[-1]["role"] == "assistant"


def test_collective_mind_self_awareness_reply(tmp_path: Path) -> None:
    db = DatabaseConnection(str(tmp_path / "test_mind.db"))
    run_migrations(db.get_connection())
    repo = MemoryRepository(db)
    mind = JarvisCollectiveMind(repo=repo)

    reply, mode = mind.think_and_reply("O que seria o Jarvis?")
    assert mode == "DEEP_CONVERSATION"
    assert "Mark Sete" in reply or "Mark VII" in reply or "Tony Stark" in reply
    assert "RTX 4060" in reply


def test_live_api_server_endpoints(tmp_path: Path) -> None:
    db = DatabaseConnection(str(tmp_path / "test_api.db"))
    run_migrations(db.get_connection())
    repo = MemoryRepository(db)
    mind = JarvisCollectiveMind(repo=repo)

    server = JarvisLiveAPIServer(mind=mind, host="127.0.0.1", port=8768)
    server.start_in_background()
    time.sleep(0.3)

    # 1. GET /api/v1/status
    req_status = urllib.request.urlopen("http://127.0.0.1:8768/api/v1/status", timeout=2.0)
    data_status = json.loads(req_status.read().decode("utf-8"))
    assert data_status["status"] == "ONLINE"
    assert "Stark Mark VII" in data_status["system"]

    # 2. GET /api/v1/memory
    req_mem = urllib.request.urlopen("http://127.0.0.1:8768/api/v1/memory", timeout=2.0)
    data_mem = json.loads(req_mem.read().decode("utf-8"))
    assert "facts" in data_mem
    assert "history" in data_mem

    # 3. GET /api/v1/telemetry
    req_telem = urllib.request.urlopen("http://127.0.0.1:8768/api/v1/telemetry", timeout=2.0)
    data_telem = json.loads(req_telem.read().decode("utf-8"))
    assert "ram_percent" in data_telem or "ram_used_gb" in data_telem

    # 4. POST /api/v1/chat
    chat_payload = json.dumps({"message": "Quem é você?", "lang": "pt"}).encode("utf-8")
    req_chat = urllib.request.Request("http://127.0.0.1:8768/api/v1/chat", data=chat_payload, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req_chat, timeout=2.0) as resp:
        data_chat = json.loads(resp.read().decode("utf-8"))
        assert "reply" in data_chat
        assert "Tony Stark" in data_chat["reply"] or "Mark" in data_chat["reply"]

    server.stop()
