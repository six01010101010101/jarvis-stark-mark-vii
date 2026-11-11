"""Grafo de Conhecimento, Entidades e Relações do Sistema inspirado no Hivemind Graph."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from jarvis.repositories.memory_repository import MemoryRepository

DEFAULT_SEEDS: list[tuple[str, str, str, str]] = [
    # (node_id, label, node_type, metadata_json)
    ("rtx_4060", "NVIDIA GeForce RTX 4060", "hardware", json.dumps({"vram": "8GB", "role": "gpu_acceleration"})),
    ("vm_central", "Máquina Virtual Central", "infrastructure", json.dumps({"role": "sandbox_and_workers"})),
    ("sqlite_db", "Banco de Dados Central SQLite", "database", json.dumps({"file": "jarvis_memory.db"})),
    ("live_api", "API Ao Vivo REST Port 8765", "service", json.dumps({"port": 8765})),
    ("steam", "Steam Games Platform", "app", json.dumps({"category": "gaming"})),
    ("discord", "Discord", "app", json.dumps({"category": "communication"})),
    ("vscode", "Visual Studio Code", "app", json.dumps({"category": "development"})),
    ("chrome", "Google Chrome", "app", json.dumps({"category": "browser"})),
    ("project_jarvis", "J.A.R.V.I.S. Mark VII", "project", json.dumps({"role": "main_assistant"})),
]

DEFAULT_EDGES: list[tuple[str, str, str, float]] = [
    # (source, target, relation, weight)
    ("project_jarvis", "rtx_4060", "utilizes", 1.0),
    ("project_jarvis", "vm_central", "connected_to", 1.0),
    ("project_jarvis", "sqlite_db", "persists_in", 1.0),
    ("project_jarvis", "live_api", "exposes", 1.0),
    ("steam", "rtx_4060", "requires_gpu", 0.9),
]


class KnowledgeGraph:
    """Motor de grafo para resolução de dependências e relações entre subsistemas e projetos."""

    def __init__(self, repo: MemoryRepository) -> None:
        self._repo = repo
        self._seed_initial_graph()

    def _seed_initial_graph(self) -> None:
        """Inicializa nós e arestas fundamentais se ainda não existirem."""
        for nid, lbl, ntype, meta in DEFAULT_SEEDS:
            self._repo.upsert_graph_node(nid, lbl, ntype, meta)
        for src, tgt, rel, w in DEFAULT_EDGES:
            self._repo.upsert_graph_edge(src, tgt, rel, w)

    def add_entity(self, node_id: str, label: str, node_type: str, metadata: dict[str, Any] | None = None) -> None:
        """Adiciona ou atualiza uma entidade no grafo de conhecimento."""
        meta_str = json.dumps(metadata or {})
        self._repo.upsert_graph_node(node_id, label, node_type, meta_str)

    def add_relation(self, source: str, target: str, relation: str, weight: float = 1.0) -> None:
        """Cria ou atualiza uma relação direcionada entre duas entidades."""
        self._repo.upsert_graph_edge(source, target, relation, weight)

    def get_related(self, entity_id: str) -> list[dict[str, Any]]:
        """Recupera arestas conectadas a uma entidade (como origem ou destino)."""
        return self._repo.get_graph_edges(source=entity_id)

    def find_connected_summary(self, query: str) -> list[str]:
        """Localiza entidades mencionadas na consulta e sintetiza suas conexões ativas."""
        q_norm = query.lower()
        insights: list[str] = []
        for nid, lbl, _, _ in DEFAULT_SEEDS:
            nid_spaced = nid.replace("_", " ")
            matches = (
                nid in q_norm
                or nid_spaced in q_norm
                or lbl.lower() in q_norm
                or any(w in q_norm for w in lbl.lower().split() if len(w) >= 4)
            )
            if matches:
                edges = self.get_related(nid)
                for e in edges:
                    src, tgt, rel = e.get("source_node"), e.get("target_node"), e.get("relation")
                    insights.append(f"{src} --[{rel}]--> {tgt}")
        return list(dict.fromkeys(insights))[:5]
