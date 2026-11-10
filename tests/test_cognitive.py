"""Testes para o motor cognitivo e comandos de aprendizagem/mapas mentais."""

from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.commands.cognitive_commands import cognitive_commands
from jarvis.commands.registry import Outcome
from jarvis.database.connection import DatabaseConnection
from jarvis.database.migrations import run_migrations
from jarvis.repositories.artifact_repository import ArtifactRepository
from jarvis.repositories.memory_repository import MemoryRepository
from jarvis.services.cognitive_engine import CognitiveEngine
from tests.fakes import FakeAnswers, make_context


@pytest.fixture
def test_env(tmp_path: Path):
    db_file = tmp_path / "test_cog.db"
    artifacts_dir = tmp_path / "artifacts"
    db = DatabaseConnection(db_file)
    run_migrations(db.get_connection())
    mem_repo = MemoryRepository(db)
    art_repo = ArtifactRepository(db)
    engine = CognitiveEngine(FakeAnswers(reply="Conteúdo gerado com sucesso."), art_repo, artifacts_dir)
    return mem_repo, art_repo, engine


def test_cognitive_engine_artifacts_generation(test_env) -> None:
    mem_repo, art_repo, engine = test_env

    # Mind map
    res = engine.generate_mind_map("Universo")
    assert "Universo" in res or "concluído" in res.lower()
    art = art_repo.get_latest_artifact("mind_map")
    assert art is not None
    assert art["title"] == "Universo"

    # Sticky notes
    res = engine.generate_sticky_notes("Python")
    assert art_repo.get_latest_artifact("sticky_notes") is not None

    # Three levels
    res = engine.explain_three_levels("Computação Quântica")
    assert art_repo.get_latest_artifact("three_levels") is not None

    # Flashcards
    res = engine.generate_flashcards("História")
    assert art_repo.get_latest_artifact("flashcards") is not None

    # Quiz
    res = engine.generate_quiz("Geografia")
    assert art_repo.get_latest_artifact("quiz") is not None

    # Study roadmap
    res = engine.generate_study_roadmap("Machine Learning")
    assert art_repo.get_latest_artifact("study_roadmap") is not None


def test_cognitive_commands_dispatch(test_env) -> None:
    mem_repo, art_repo, engine = test_env
    ctx = make_context(memory=mem_repo, artifacts=art_repo, cognitive=engine)

    cmd_map = {cmd.name: cmd for cmd in cognitive_commands()}

    # Test Mind Map voice trigger
    cmd = cmd_map["mind_map"]
    assert cmd.matches("crie um mapa mental sobre inteligência artificial")
    assert cmd.handler(ctx, "crie um mapa mental sobre inteligência artificial") is Outcome.CONTINUE

    # Test Memory "lembre-se" trigger
    cmd_mem = cmd_map["remember"]
    assert cmd_mem.matches("lembre se que meu jogo favorito e fortnite")
    assert cmd_mem.handler(ctx, "lembre-se que meu jogo favorito é fortnite") is Outcome.CONTINUE
    assert mem_repo.get_memory("meu jogo favorito") == "fortnite"

    # Test Memory recall trigger
    cmd_recall = cmd_map["recall_memory"]
    assert cmd_recall.matches("o que voce sabe sobre mim")
    assert cmd_recall.handler(ctx, "o que você sabe sobre mim") is Outcome.CONTINUE
