"""Testes da máquina de estados e telemetria operacional."""

from __future__ import annotations

from jarvis.services.telemetry_state_machine import AssistantState, TelemetryStateMachine


def test_initial_state_idle() -> None:
    sm = TelemetryStateMachine()
    assert sm.current_state is AssistantState.IDLE


def test_state_transitions() -> None:
    sm = TelemetryStateMachine()
    events: list[tuple[AssistantState, AssistantState, str]] = []

    def on_change(from_s: AssistantState, to_s: AssistantState, reason: str) -> None:
        events.append((from_s, to_s, reason))

    sm.subscribe(on_change)

    # 1. IDLE -> LISTENING
    assert sm.transition_to(AssistantState.LISTENING, "wake_word") is True
    assert sm.current_state is AssistantState.LISTENING

    # 2. Transição para o mesmo estado não deve disparar evento
    assert sm.transition_to(AssistantState.LISTENING, "redundant") is False

    # 3. LISTENING -> PROCESSING -> SPEAKING -> IDLE
    assert sm.transition_to(AssistantState.PROCESSING, "executing") is True
    assert sm.transition_to(AssistantState.SPEAKING, "replying") is True
    assert sm.transition_to(AssistantState.IDLE, "ready") is True

    assert len(events) == 4
    assert events[0] == (AssistantState.IDLE, AssistantState.LISTENING, "wake_word")
    assert events[-1] == (AssistantState.SPEAKING, AssistantState.IDLE, "ready")


def test_telemetry_snapshot_and_history() -> None:
    sm = TelemetryStateMachine(max_history=10)
    sm.transition_to(AssistantState.LISTENING, "step1")
    sm.transition_to(AssistantState.PROCESSING, "step2")

    history = sm.get_history()
    assert len(history) == 2
    assert history[0].reason == "step1"
    assert history[1].reason == "step2"

    snapshot = sm.get_telemetry_snapshot()
    assert snapshot["current_state"] == "PROCESSING"
    assert snapshot["transitions_count"] == 2
    assert snapshot["uptime_seconds"] >= 0.0


def test_unsubscribe_listener() -> None:
    sm = TelemetryStateMachine()
    called = []

    def observer(_from: AssistantState, _to: AssistantState, _reason: str) -> None:
        called.append(True)

    sm.subscribe(observer)
    sm.transition_to(AssistantState.LISTENING)
    assert len(called) == 1

    sm.unsubscribe(observer)
    sm.transition_to(AssistantState.IDLE)
    assert len(called) == 1  # Não deve ser chamado novamente
