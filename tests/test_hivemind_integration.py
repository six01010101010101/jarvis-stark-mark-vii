"""Testes unitários e de integração dos módulos cognitivos Hivemind do J.A.R.V.I.S."""

from __future__ import annotations

import sqlite3
import pytest

from jarvis.commands import CommandContext, build_registry
from jarvis.database.connection import DatabaseConnection
from jarvis.database.migrations import run_migrations
from jarvis.repositories.memory_repository import MemoryRepository
from jarvis.services.collective_mind import JarvisCollectiveMind
from jarvis.services.goal_tracker import GoalTracker
from jarvis.services.hivemind_coordinator import HivemindCoordinator
from jarvis.services.knowledge_graph import KnowledgeGraph
from jarvis.services.lexical_recall import LexicalRecallEngine, extract_bigrams, tokenize


@pytest.fixture
def test_repo(tmp_path) -> MemoryRepository:
    db_file = tmp_path / "test_hivemind.db"
    conn = sqlite3.connect(str(db_file), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    run_migrations(conn)

    class FakeDBConnection(DatabaseConnection):
        def __init__(self, c: sqlite3.Connection):
            self._c = c
        def get_connection(self) -> sqlite3.Connection:
            return self._c

    return MemoryRepository(FakeDBConnection(conn))


def test_tokenizer_and_bigrams():
    text = "Jarvis, crie a nova interface com IA e banco"
    tokens = tokenize(text)
    assert "jarvis" in tokens
    assert "crie" in tokens
    assert "interface" in tokens
    assert "banco" in tokens
    assert "com" not in tokens  # Stop word

    bigrams = extract_bigrams(["nova", "interface", "grafica"])
    assert ("nova", "interface") in bigrams
    assert ("interface", "grafica") in bigrams


def test_lexical_recall_bm25(test_repo: MemoryRepository):
    test_repo.set_memory("rtx_status", "Placa de video RTX 4060 com 8GB VRAM em operacao nominal")
    test_repo.save_episodic_turn("Como esta a GPU?", "A RTX 4060 esta fria e pronta.")

    engine = LexicalRecallEngine(test_repo)
    results = engine.recall("informacoes sobre a GPU RTX 4060")

    assert len(results) > 0
    assert any("RTX 4060" in r for r in results)


def test_goal_tracker_lifecycle(test_repo: MemoryRepository):
    tracker = GoalTracker(test_repo)

    g1 = tracker.add_goal(title="Refatorar Modulo de Voz", description="Aplicar VAD mais rapido", priority=3)
    assert g1.status == "opened"

    active = tracker.list_goals(status="opened")
    assert len(active) >= 1
    assert any(g.title == "Refatorar Modulo de Voz" for g in active)

    spoken = tracker.format_summary_spoken()
    assert "Refatorar Modulo de Voz" in spoken

    success = tracker.complete_goal("Refatorar Modulo de Voz")
    assert success is True

    completed = tracker.list_goals(status="completed")
    assert any(g.title == "Refatorar Modulo de Voz" for g in completed)


def test_knowledge_graph(test_repo: MemoryRepository):
    graph = KnowledgeGraph(test_repo)
    graph.add_entity("steam_game", "Cyberpunk 2077", "game")
    graph.add_relation("steam_game", "rtx_4060", "requires_gpu", weight=1.0)

    related = graph.get_related("steam_game")
    assert len(related) >= 1
    assert related[0]["relation"] == "requires_gpu"

    summary = graph.find_connected_summary("Quero jogar no RTX 4060")
    assert len(summary) >= 1


def test_hivemind_coordinator_tangent_and_context(test_repo: MemoryRepository):
    coord = HivemindCoordinator(test_repo)

    tangent_reply = coord.capture_tangent_if_present("Jarvis, lembre de comprar mais pasta termica")
    assert tangent_reply is not None
    assert "comprar mais pasta termica" in tangent_reply

    context = coord.build_augmented_context("pasta termica e GPU")
    assert "recalled_prompt_block" in context
    assert "active_goals_block" in context
    assert "comprar mais pasta termica" in context["active_goals_block"]


def test_collective_mind_hivemind_integration(test_repo: MemoryRepository):
    mind = JarvisCollectiveMind(repo=test_repo, gemini_service=None)

    # Tangente detectada
    reply, mode = mind.think_and_reply("Jarvis, anote a meta de otimizar o banco de dados")
    assert mode == "TASK_CAPTURE"
    assert "otimizar o banco de dados" in reply

    # Pergunta profunda acionando raciocínio aumentado
    reply2, mode2 = mind.think_and_reply("Jarvis, qual arquitetura devemos seguir para escalar?")
    assert mode2 == "DEEP_CONVERSATION"
    assert "senhor" in reply2.lower()


def test_goal_voice_commands(test_repo: MemoryRepository):
    from unittest.mock import MagicMock
    registry = build_registry()

    cmd = registry.find("minhas metas")
    assert cmd is not None

    mock_speaker = MagicMock()
    mock_view = MagicMock()
    ctx = CommandContext(
        speaker=mock_speaker, listener=MagicMock(), view=mock_view, answers=MagicMock(),
        messages=MagicMock(), launcher=MagicMock(), processes=MagicMock(), memory=test_repo,
    )

    cmd.handler(ctx, "quais sao minhas metas")
    mock_speaker.say.assert_called_once()
