"""Coordenador da Mente Coletiva Hivemind (Recall Proativo, Metas e Grafo)."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from jarvis.services.goal_tracker import GoalTracker
from jarvis.services.knowledge_graph import KnowledgeGraph
from jarvis.services.lexical_recall import LexicalRecallEngine

if TYPE_CHECKING:
    from jarvis.repositories.memory_repository import MemoryRepository

TANGENT_PATTERNS = [
    r"\b(?:salve a tarefa|crie a tarefa|adicione a tarefa|anote a tarefa)\s+(?:de\s+)?(.+)",
    r"\b(?:salve a meta|crie a meta|adicione a meta|anote a meta)\s+(?:de\s+)?(.+)",
    r"\b(?:lembre-se de|lembre de|guarde para depois|guarde que eu preciso)\s+(.+)",
]


class HivemindCoordinator:
    """Orquestrador central dos subsistemas Hivemind integrados à arquitetura Stark."""

    def __init__(self, repo: MemoryRepository) -> None:
        self.repo = repo
        self.recall = LexicalRecallEngine(repo)
        self.goals = GoalTracker(repo)
        self.graph = KnowledgeGraph(repo)

    def capture_tangent_if_present(self, utterance: str) -> str | None:
        """Identifica e captura tarefas ou metas expressas em tangentes de diálogo."""
        for pattern in TANGENT_PATTERNS:
            match = re.search(pattern, utterance, flags=re.IGNORECASE)
            if match:
                task_title = match.group(1).strip()
                if len(task_title) >= 3:
                    goal = self.goals.add_goal(title=task_title, priority=2, category="captura_tangente")
                    return f"Entendido, senhor. Registrei a meta '{goal.title}' em sua lista de objetivos."
        return None

    def build_augmented_context(self, query: str) -> dict[str, Any]:
        """Constrói o bloco cognitivo aumentado combinando BM25, metas ativas e grafo."""
        recalled = self.recall.recall(query, top_k=5)
        active_goals = self.goals.format_active_goals_for_prompt(limit=4)
        graph_links = self.graph.find_connected_summary(query)

        recalled_text = "\n".join(f"- {item}" for item in recalled) if recalled else "Nenhuma memória associada diretamente."
        graph_text = "\n".join(f"- {link}" for link in graph_links) if graph_links else "Nenhuma dependência crítica associada."

        return {
            "recalled_items": recalled,
            "recalled_prompt_block": recalled_text,
            "active_goals_block": active_goals,
            "graph_prompt_block": graph_text,
        }
