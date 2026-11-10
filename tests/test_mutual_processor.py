"""Testes unitários do motor fonético e do processador mútuo de máquina."""

from __future__ import annotations

from jarvis.commands import Outcome, build_registry
from jarvis.services.machine_state import MachineSnapshot, MachineStateMonitor
from jarvis.services.mutual_processor import MutualProcessor
from jarvis.services.phonetic_engine import PhoneticEngine, phonetic_key
from tests.fakes import make_context


class FakeMachineMonitor(MachineStateMonitor):
    def __init__(self, high_ram: bool = False, low_disk: bool = False) -> None:
        self.high_ram = high_ram
        self.low_disk = low_disk

    def get_snapshot(self) -> MachineSnapshot:
        return {
            "active_window": "Visual Studio Code",
            "ram_used_gb": 14.5 if self.high_ram else 6.2,
            "ram_free_gb": 1.5 if self.high_ram else 9.8,
            "ram_percent": 88 if self.high_ram else 38,
            "disk_free_gb": 8.0 if self.low_disk else 250.0,
            "power_status": "conectado à tomada",
            "is_charging": True,
        }

    def get_active_window_title(self) -> str:
        return "Fortnite"

    def optimize_system_memory(self) -> int:
        return 1

    def get_memory_metrics(self) -> tuple[float, float, int]:
        return 5.8, 10.2, 36


def test_phonetic_engine_transformations() -> None:
    engine = PhoneticEngine()

    assert phonetic_key("bloco") == phonetic_key("bloku")
    assert engine.normalize_utterance("abrir fortinaite") == "abrir fortnite"
    assert engine.normalize_utterance("abrir bloco dinota") == "abrir bloco de notas"
    assert engine.normalize_utterance("tocar ispotifai") == "tocar spotify"
    assert engine.normalize_utterance("abrir calque") == "abrir calculadora"


def test_mutual_processor_healthy_state() -> None:
    processor = MutualProcessor(FakeMachineMonitor(high_ram=False))
    health = processor.get_machine_health_report()
    assert "Visual Studio Code" in health
    assert "6.2" in health

    needs = processor.diagnose_current_needs()
    assert "equilíbrio perfeito" in needs


def test_mutual_processor_critical_needs() -> None:
    processor = MutualProcessor(FakeMachineMonitor(high_ram=True, low_disk=True))
    needs = processor.diagnose_current_needs()
    assert "consumo de memória" in needs
    assert "partição C" in needs


def test_machine_commands_dispatch() -> None:
    ctx = make_context()
    registry = build_registry()

    outcome_status = registry.dispatch(ctx, "como esta a maquina")
    assert outcome_status is Outcome.CONTINUE
    assert len(ctx.speaker.spoken) >= 1  # type: ignore[attr-defined]

    outcome_screen = registry.dispatch(ctx, "o que estou usando")
    assert outcome_screen is Outcome.CONTINUE
    assert len(ctx.speaker.spoken) >= 2  # type: ignore[attr-defined]

    outcome_opt = registry.dispatch(ctx, "otimizar computador")
    assert outcome_opt is Outcome.CONTINUE
    assert len(ctx.speaker.spoken) >= 3  # type: ignore[attr-defined]
