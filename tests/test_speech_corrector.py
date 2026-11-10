"""Testes unitários para o motor de autocorreção fonética e semântica do Jarvis."""

from __future__ import annotations

import pytest

from jarvis.services.speech_corrector import SpeechCorrector


@pytest.fixture
def corrector() -> SpeechCorrector:
    return SpeechCorrector()


def test_repair_wake_word_phonetic_variations(corrector: SpeechCorrector) -> None:
    # "chave" -> "jarvis"
    assert corrector.repair_wake_word("chave abrir bloco de notas").startswith("jarvis")
    # "garvis" -> "jarvis"
    assert corrector.repair_wake_word("garvis tocar musica").startswith("jarvis")
    # "já" -> "jarvis"
    assert corrector.repair_wake_word("já fechar navegador").startswith("jarvis")
    # "jarbas" -> "jarvis"
    assert corrector.repair_wake_word("jarbas como você está").startswith("jarvis")


def test_expand_game_and_app_abbreviations(corrector: SpeechCorrector) -> None:
    # "fort" -> "fortnite"
    assert corrector.expand_abbreviations("abrir fort") == "abrir fortnite"
    assert corrector.expand_abbreviations("jarvis abrir fort") == "jarvis abrir fortnite"

    # "mine" -> "minecraft"
    assert corrector.expand_abbreviations("jogar mine") == "jogar minecraft"

    # "bloco dinota" -> "bloco de notas"
    assert corrector.expand_abbreviations("abrir bloco dinota") == "abrir bloco de notas"
    assert corrector.expand_abbreviations("abrir bloco de nota") == "abrir bloco de notas"

    # "zap" / "whats" -> "whatsapp"
    assert corrector.expand_abbreviations("abrir zap") == "abrir whatsapp"
    assert corrector.expand_abbreviations("mandar mensagem no whats") == "mandar mensagem no whatsapp"

    # "tube" -> "youtube"
    assert corrector.expand_abbreviations("abrir tube") == "abrir youtube"


def test_pipeline_correction(corrector: SpeechCorrector) -> None:
    # Corrige tanto a wake word distorcida quanto a abreviação do jogo
    result = corrector.correct("chave abrir fort")
    assert result == "jarvis abrir fortnite"

    result_zap = corrector.correct("garvis abrir zap")
    assert result_zap == "jarvis abrir whatsapp"
