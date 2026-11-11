"""Motor de Recall Léxico BM25 com Tokenização e Bi-gramas inspirado no Hivemind."""

from __future__ import annotations

import math
import re
from typing import TYPE_CHECKING, Sequence

from jarvis.text_utils import normalize

if TYPE_CHECKING:
    from jarvis.repositories.memory_repository import MemoryRepository

STOP_WORDS = frozenset({
    "a", "ao", "aos", "as", "com", "da", "das", "de", "do", "dos", "e", "em", "na",
    "nas", "no", "nos", "o", "os", "para", "por", "que", "se", "um", "uma", "uns",
    "umas", "the", "and", "or", "in", "on", "at", "to", "for", "of", "with", "is",
})

K1 = 1.2
B = 0.75


def tokenize(text: str) -> list[str]:
    """Extrai tokens normalizados filtrando pontuações e stop-words."""
    norm = normalize(text).lower()
    raw_tokens = re.findall(r"\b[a-z0-9_]{2,}\b", norm)
    return [t for t in raw_tokens if t not in STOP_WORDS]


def extract_bigrams(tokens: Sequence[str]) -> set[tuple[str, str]]:
    """Gera pares adjacentes de termos para validação de proximidade de frase."""
    if len(tokens) < 2:
        return set()
    return {(tokens[i], tokens[i + 1]) for i in range(len(tokens) - 1)}


class LexicalRecallEngine:
    """Índice local e mecanismo de ranqueamento BM25 com reforço de bi-gramas."""

    def __init__(self, repo: MemoryRepository) -> None:
        self._repo = repo

    def recall(self, query: str, top_k: int = 5) -> list[str]:
        """Recupera proativamente as memórias e fatos mais relevantes para a oração."""
        q_tokens = tokenize(query)
        if not q_tokens:
            return []

        docs = self._collect_documents()
        if not docs:
            return []

        q_bigrams = extract_bigrams(q_tokens)
        doc_tokens_list = [tokenize(doc) for doc in docs]
        n_docs = len(docs)
        avg_doc_len = max(1.0, sum(len(dt) for dt in doc_tokens_list) / max(1, n_docs))

        # Frequência de documento de cada termo da query
        df: dict[str, int] = {}
        for term in set(q_tokens):
            df[term] = sum(1 for dt in doc_tokens_list if term in dt)

        # Cálculo do score BM25 + bônus de bi-grama
        scored: list[tuple[float, str]] = []
        for doc, d_tokens in zip(docs, doc_tokens_list):
            if not d_tokens:
                continue
            doc_len = len(d_tokens)
            score = 0.0
            term_counts: dict[str, int] = {}
            for t in d_tokens:
                term_counts[t] = term_counts.get(t, 0) + 1

            for q_term in set(q_tokens):
                tf = term_counts.get(q_term, 0)
                if tf == 0:
                    continue
                doc_freq = df.get(q_term, 0)
                idf = math.log(1.0 + (n_docs - doc_freq + 0.5) / (doc_freq + 0.5))
                num = tf * (K1 + 1.0)
                denom = tf + K1 * (1.0 - B + B * (doc_len / avg_doc_len))
                score += idf * (num / denom)

            # Reforço por bi-gramas coincidentes
            if q_bigrams:
                doc_bigrams = extract_bigrams(d_tokens)
                shared_bigrams = len(q_bigrams.intersection(doc_bigrams))
                score += shared_bigrams * 1.5

            if score > 0.05:
                scored.append((score, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored[:top_k]]

    def _collect_documents(self) -> list[str]:
        """Reúne fatos semânticos, histórico episódico recente e metas ativas."""
        corpus: list[str] = []
        try:
            facts = self._repo.get_learned_facts(limit=30)
            corpus.extend(facts)
        except Exception:
            pass

        try:
            memories = self._repo.get_all_memories()
            corpus.extend(f"{m.get('key', '')}: {m.get('value', '')}" for m in memories)
        except Exception:
            pass

        try:
            goals = self._repo.get_goals(limit=20)
            corpus.extend(f"Meta ({g.get('status')}): {g.get('title')} - {g.get('description')}" for g in goals)
        except Exception:
            pass

        try:
            episodes = self._repo.get_recent_episodic_context(limit=20)
            corpus.extend(f"{e.get('role')}: {e.get('content')}" for e in episodes)
        except Exception:
            pass

        return list(dict.fromkeys(corpus))  # Deduplicação preservando ordem
