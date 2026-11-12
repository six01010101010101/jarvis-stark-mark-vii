"""Testes do sistema operacional, conjugação linguística, N8N, piadas e controle de janelas."""

from __future__ import annotations

from jarvis.commands.joke_commands import TECH_JOKES, joke_commands
from jarvis.commands.window_navigation_commands import window_navigation_commands
from jarvis.services.barge_in_listener import BargeInListener
from jarvis.services.conversation_session import ConversationSession
from jarvis.services.conversational_engine import ConversationalEngine
from jarvis.services.linguistic_conjugator import LinguisticConjugator
from jarvis.services.local_brain import LocalStarkBrain
from jarvis.services.n8n_integration import N8NWorkflowConnector
from jarvis.services.window_switcher import WindowSwitcher


def test_linguistic_conjugator_phonetics_and_verbs() -> None:
    # 1. Abecedário e fonética
    assert LinguisticConjugator.get_letter_phonetic("h") == "agá"
    assert LinguisticConjugator.get_letter_phonetic("w") == "dáblio"
    assert "jota" in LinguisticConjugator.spell_phonetic("jarvis")

    # 2. Verbos de abertura
    assert LinguisticConjugator.is_open_intent("abra") is True
    assert LinguisticConjugator.is_open_intent("inicie") is True
    assert LinguisticConjugator.is_open_intent("execute") is True
    assert LinguisticConjugator.is_open_intent("rodar") is True
    assert LinguisticConjugator.is_open_intent("bota") is True

    # 3. Verbos de fechamento
    assert LinguisticConjugator.is_close_intent("feche") is True
    assert LinguisticConjugator.is_close_intent("encerre") is True
    assert LinguisticConjugator.is_close_intent("termine") is True
    assert LinguisticConjugator.is_close_intent("finalizar") is True

    # 4. Extração de ação e alvo
    act_open, target_open = LinguisticConjugator.extract_action_and_target("abra o fortnite")
    assert act_open == "open"
    assert target_open == "fortnite"

    act_close, target_close = LinguisticConjugator.extract_action_and_target("encerre o discord")
    assert act_close == "close"
    assert target_close == "discord"

    act_switch, target_switch = LinguisticConjugator.extract_action_and_target("mudar para o chrome")
    assert act_switch == "switch"
    assert "chrome" in target_switch


def test_barge_in_voice_interrupt() -> None:
    stopped = False

    def on_stop() -> None:
        nonlocal stopped
        stopped = True

    listener = BargeInListener(on_stop_callback=on_stop)
    assert listener.is_stop_phrase("jarvis pare") is True
    assert listener.is_stop_phrase("pare de falar jarvis") is True
    assert listener.is_stop_phrase("pare jarvis") is True
    assert listener.is_stop_phrase("bom dia jarvis") is False

    assert listener.notify_utterance("pare de falar jarvis") is True
    assert stopped is True


def test_n8n_integration_offline_resilience() -> None:
    connector = N8NWorkflowConnector("http://127.0.0.1:59999/webhook/fake")
    assert connector.check_connection() is False

    result = connector.trigger_workflow("sync_data", {"key": "val"})
    assert result["status"] in ("offline", "error")

    # Payload gigante bloqueado por segurança
    huge_payload = {"data": "x" * 70000}
    blocked = connector.trigger_workflow("overflow", huge_payload)
    assert blocked["status"] == "error"


def test_window_switcher_safety_and_actions() -> None:
    # Ataque de injeção no switch deve ser barrado com segurança
    assert WindowSwitcher.switch_to_app("chrome & calc.exe") is False
    assert WindowSwitcher.switch_to_app("app; rm -rf") is False

    # Disparos de automação nativa do Windows (não devem levantar exceção)
    assert isinstance(WindowSwitcher.trigger_alt_tab(), bool)
    assert isinstance(WindowSwitcher.show_desktop(), bool)


def test_conversation_session_15s_and_assistance() -> None:
    session = ConversationSession(timeout_seconds=15.0)
    assert session.patience_seconds == 15.0
    assert session.is_assistance_trigger("jarvis me ajude") is True
    assert session.is_assistance_trigger("me ajuda com um problema") is True
    assert session.is_assistance_trigger("como está o tempo") is False


def test_tone_detection_and_jokes() -> None:
    assert ConversationalEngine.detect_tone("kkk to só de brincadeira") == "HUMOR"
    assert ConversationalEngine.detect_tone("isso é urgente e muito sério") == "SERIOUS"
    assert ConversationalEngine.detect_tone("quanto é dois mais dois") == "NEUTRAL"

    # Piadas reais disponíveis
    assert len(TECH_JOKES) >= 5
    assert any("programador" in j.lower() or "binário" in j.lower() for j in TECH_JOKES)

    cmds = joke_commands()
    assert any(cmd.name == "tell_funny_joke" for cmd in cmds)


def test_local_brain_multi_verbs_and_app_launch() -> None:
    # Abertura com múltiplos verbos conjugados
    res_fortnite = LocalStarkBrain.resolve_intent("abra o fortnite")
    assert res_fortnite["action"] == "open_app"
    assert "fortnite" in res_fortnite["target"].lower()

    res_inicie = LocalStarkBrain.resolve_intent("inicie o bloco de notas")
    assert res_inicie["action"] == "open_app"
    assert "notepad" in res_inicie["target"]

    # Fechamento com verbos conjugados
    res_close = LocalStarkBrain.resolve_intent("encerre o discord")
    assert res_close["action"] == "close_app"
    assert res_close["target"] == "discord"

    # Navegação de telas
    nav_cmds = window_navigation_commands()
    assert any(cmd.name == "alt_tab_switch" for cmd in nav_cmds)
    assert any(cmd.name == "show_desktop_screen" for cmd in nav_cmds)
    assert any(cmd.name == "open_task_manager_screen" for cmd in nav_cmds)
