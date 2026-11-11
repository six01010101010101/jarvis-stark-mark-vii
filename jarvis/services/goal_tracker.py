"""Gerenciador de Metas, Tarefas e Tangentes inspirado no Hivemind Goals."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from jarvis.repositories.memory_repository import MemoryRepository


@dataclass(frozen=True)
class Goal:
    """Representação de um objetivo ou tarefa do usuário."""

    goal_id: str
    title: str
    description: str
    status: str
    priority: int
    category: str
    created_at: str


class GoalTracker:
    """Gerenciamento de ciclo de vida de metas (aberta, em andamento, concluída)."""

    def __init__(self, repo: MemoryRepository) -> None:
        self._repo = repo

    def add_goal(self, title: str, description: str = "", priority: int = 1, category: str = "geral") -> Goal:
        """Registra uma nova meta com identificador gerado a partir do título."""
        slug = re.sub(r"[^\w\s-]", "", title.lower()).strip()
        slug = re.sub(r"[-\s]+", "-", slug)[:32]
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        goal_id = f"goal_{slug}_{timestamp}" if slug else f"goal_{timestamp}"
        now_str = datetime.now().isoformat()

        self._repo.save_goal(
            goal_id=goal_id,
            title=title.strip(),
            description=description.strip(),
            status="opened",
            priority=priority,
            category=category.strip(),
        )
        return Goal(goal_id, title.strip(), description.strip(), "opened", priority, category.strip(), now_str)

    def list_goals(self, status: str | None = None, limit: int = 10) -> list[Goal]:
        """Recupera metas ordenadas por prioridade e data."""
        rows = self._repo.get_goals(status=status, limit=limit)
        return [
            Goal(
                goal_id=str(r.get("goal_id", "")),
                title=str(r.get("title", "")),
                description=str(r.get("description", "")),
                status=str(r.get("status", "opened")),
                priority=int(r.get("priority", 1)),
                category=str(r.get("category", "geral")),
                created_at=str(r.get("created_at", "")),
            )
            for r in rows
        ]

    def complete_goal(self, identifier: str) -> bool:
        """Marca uma meta como concluída por ID ou por busca de título aproximada."""
        return self._repo.update_goal_status(identifier, "completed")

    def format_active_goals_for_prompt(self, limit: int = 5) -> str:
        """Formata metas abertas ou em andamento para injeção no prompt de raciocínio."""
        goals = self.list_goals(status="opened", limit=limit)
        if not goals:
            return "Nenhuma meta ativa no momento."
        lines: list[str] = []
        for g in goals:
            desc = f" ({g.description})" if g.description else ""
            lines.append(f"- [P{g.priority}] {g.title}{desc}")
        return "\n".join(lines)

    def format_summary_spoken(self) -> str:
        """Formata um resumo auditivo conciso e natural para o Jarvis falar."""
        goals = self.list_goals(status="opened", limit=5)
        if not goals:
            return "Você não possui nenhuma meta pendente registrada no momento, senhor. Gostaria de definir um novo objetivo?"
        count = len(goals)
        items = ", ".join(f"'{g.title}'" for g in goals[:3])
        more = f" e mais {count - 3} itens" if count > 3 else ""
        return f"Você tem {count} {'meta ativa' if count == 1 else 'metas ativas'} registradas, senhor: {items}{more}."
