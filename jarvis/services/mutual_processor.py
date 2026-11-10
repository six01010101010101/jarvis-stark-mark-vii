"""Processador mútuo: correlaciona intenções do usuário com o estado profundo da máquina."""

from __future__ import annotations

import logging
from jarvis.services.machine_state import MachineSnapshot, MachineStateMonitor

logger = logging.getLogger(__name__)


class MutualProcessor:
    """Atua como processador central Stark correlacionando atividade e saúde do PC."""

    def __init__(self, monitor: MachineStateMonitor | None = None) -> None:
        self._monitor = monitor or MachineStateMonitor()

    def get_machine_health_report(self) -> str:
        """Gera relatório holístico do estado operacional da máquina."""
        snap: MachineSnapshot = self._monitor.get_snapshot()
        return (
            f"Senhor Ken, a estação acusa operação estável. "
            f"A janela ativa no momento é '{snap['active_window']}'. "
            f"A memória física está com {snap['ram_used_gb']} gigabytes em uso ({snap['ram_percent']}%), "
            f"restando {snap['ram_free_gb']} gigabytes livres. "
            f"O disco C dispõe de {snap['disk_free_gb']} gigabytes e a alimentação acusa {snap['power_status']}."
        )

    def diagnose_current_needs(self) -> str:
        """Avalia proativamente o que o usuário ou a máquina precisam no momento."""
        snap: MachineSnapshot = self._monitor.get_snapshot()
        needs: list[str] = []

        if snap["ram_percent"] >= 80:
            needs.append(
                f"o consumo de memória física está em nível crítico ({snap['ram_percent']}%). "
                f"Sugiro executar o comando de otimização para liberar recursos"
            )

        if snap["disk_free_gb"] < 15.0:
            needs.append(
                f"a partição C dispõe de apenas {snap['disk_free_gb']} gigabytes livres. "
                f"Recomendo limpeza de arquivos temporários"
            )

        if not snap["is_charging"] and "bateria" in snap["power_status"]:
            needs.append("o computador está operando na bateria. Considere conectar o carregador")

        if not needs:
            return (
                f"Senhor Ken, seus sistemas estão em equilíbrio perfeito. "
                f"Você tem {snap['ram_free_gb']} gigabytes de memória livres e a janela atual é '{snap['active_window']}'. "
                f"Você não possui gargalos técnicos. Em que posso auxiliá-lo agora?"
            )

        joined_needs = "; além disso, ".join(needs)
        return f"Senhor Ken, avaliei o estado da máquina e identifiquei que {joined_needs}."

    def report_current_screen(self) -> str:
        """Informa qual aplicativo ou janela o usuário está utilizando agora."""
        active = self._monitor.get_active_window_title()
        return f"No momento, a janela em primeiro plano na sua tela é '{active}', senhor."

    def execute_mutual_optimization(self) -> str:
        """Executa protocolo de autocura, aparamento de páginas ociosas e descarte de lixo."""
        self._monitor.optimize_system_memory()
        used_ram, free_ram, ram_pct = self._monitor.get_memory_metrics()
        return (
            f"Protocolo de autocura concluído, senhor Ken. Conjuntos ociosos de memória foram descarregados. "
            f"A memória em uso agora é de {used_ram} gigabytes ({ram_pct}%), com {free_ram} gigabytes livres."
        )
