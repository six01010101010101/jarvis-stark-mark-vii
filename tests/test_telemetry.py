"""Testes unitários para telemetria de hardware e saúde do PC em tempo real."""

from __future__ import annotations

import pytest

from jarvis.services.telemetry import SystemTelemetry


@pytest.fixture
def telemetry() -> SystemTelemetry:
    return SystemTelemetry()


def test_memory_status_returns_positive_numbers(telemetry: SystemTelemetry) -> None:
    total, used, free = telemetry.get_memory_status()
    assert total > 0.5
    assert used >= 0.0
    assert free >= 0.0
    assert abs((used + free) - total) < 1.0


def test_disk_status_returns_positive_numbers(telemetry: SystemTelemetry) -> None:
    total, used, free = telemetry.get_disk_status()
    assert total > 1.0
    assert free > 0.0
    assert used > 0.0


def test_full_telemetry_report_contains_stark_diagnostics(telemetry: SystemTelemetry) -> None:
    report = telemetry.get_full_report()
    assert "senhor" in report.lower()
    assert "gb" in report.lower() or "disco" in report.lower()
    assert "memória" in report.lower() or "sistemas" in report.lower()
