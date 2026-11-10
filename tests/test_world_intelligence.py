"""Testes unitários para inteligência de mundo real: matemática, horário, clima e fatos."""

from __future__ import annotations

import pytest

from jarvis.services.world_intelligence import WorldIntelligence
from tests.fakes import FakeAnswers


@pytest.fixture
def intelligence() -> WorldIntelligence:
    return WorldIntelligence(answers=FakeAnswers(reply="Resposta factual precisa."))


def test_evaluate_math_expressions(intelligence: WorldIntelligence) -> None:
    # 25 + 17
    assert "42" in intelligence.evaluate_math("quanto é 25 mais 17")
    # 50 * 4
    assert "200" in intelligence.evaluate_math("calcule 50 vezes 4")
    # 100 / 5
    assert "20" in intelligence.evaluate_math("quanto é 100 dividido por 5")
    # Expressão não matemática
    assert intelligence.evaluate_math("abrir bloco de notas") is None


def test_get_current_time_and_date(intelligence: WorldIntelligence) -> None:
    time_str = intelligence.get_time_report()
    assert "horas" in time_str or "minuto" in time_str or ":" in time_str
    date_str = intelligence.get_date_report()
    assert "2026" in date_str or "feira" in date_str.lower() or "dia" in date_str.lower()


def test_answer_direct_factual_query(intelligence: WorldIntelligence) -> None:
    ans = intelligence.answer_direct("qual é a distância da Terra até a Lua?")
    assert ans == "Resposta factual precisa."
