"""Testes de Conhecimento Geral e Provedores Multi-IA (Gemini 3.5, Idade da Terra e Fonética)."""

from __future__ import annotations

import os
from pathlib import Path

from jarvis.services.conversational_engine import ConversationalEngine
from jarvis.services.gemini_service import GeminiAnswerService
from jarvis.services.local_brain import LocalStarkBrain
from jarvis.services.multi_ai_supplier import MultiAISupplierOrchestrator


def test_g_ai_desktop_integration_present() -> None:
    g_ai_path = Path(__file__).resolve().parent.parent / "integrations" / "g-ai-desktop"
    assert g_ai_path.exists()
    assert (g_ai_path / "package.json").exists()
    assert (g_ai_path / "src" / "main" / "suppliers" / "GeminiSupplier.js").exists()


def test_multi_ai_supplier_orchestrator() -> None:
    suppliers = MultiAISupplierOrchestrator.list_suppliers()
    assert len(suppliers) >= 3
    assert any("Gemini" in s for s in suppliers)

    # Limpeza fonética para sintetizador de voz (sem markdown feio na fala)
    raw = "A Terra tem **4,5 bilhões de anos**! Veja mais em `#ciência`."
    clean = MultiAISupplierOrchestrator._clean_phonetic_text(raw)
    assert "**" not in clean
    assert "#" not in clean
    assert "4,5 bilhões de anos" in clean


def test_earth_age_knowledge_response() -> None:
    engine = ConversationalEngine()
    reply = engine.generate_reply("quantos anos a Terra tem?")
    assert "4,5" in reply or "bilhões de anos" in reply.lower()
    assert "terra" in reply.lower()


def test_local_brain_answers_earth_age_without_random_stuff() -> None:
    res = LocalStarkBrain.resolve_intent("quantos anos a Terra tem?")
    assert res["action"] == "chat"
    assert "4,5" in res["reply"] or "bilhões de anos" in res["reply"].lower()


def test_gemini_service_uses_active_model() -> None:
    service = GeminiAnswerService(api_key="test_key", model="gemini-3.5-flash-lite")
    assert "3.5" in service._model or "2.5" in service._model
    assert "2.0" not in service._model
