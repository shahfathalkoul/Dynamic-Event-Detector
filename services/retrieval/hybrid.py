"""Dependency-light hybrid retriever for local RAG tests.

The production implementation should combine PostgreSQL full-text search,
Qdrant vector search, metadata filters, and reranking. This module provides the
same shape in memory so agent workflows and APIs can be exercised today.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from math import sqrt

from src.preprocessing import clean_text


@dataclass(frozen=True)
class RetrievedDocument:
    document_id: str
    text: str
    score: float
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class IndexedDocument:
    document_id: str
    text: str
    metadata: dict
    term_counts: Counter[str]


class HybridRetriever:
    """Simple lexical/vector-like retriever with metadata filtering."""

    def __init__(self) -> None:
        self._documents: dict[str, IndexedDocument] = {}

    def add_document(self, document_id: str, text: str, metadata: dict | None = None) -> None:
        tokens = clean_text(text).split()
        self._documents[document_id] = IndexedDocument(
            document_id=document_id,
            text=text,
            metadata=metadata or {},
            term_counts=Counter(tokens),
        )

    def add_many(self, documents: list[tuple[str, str, dict]]) -> None:
        for document_id, text, metadata in documents:
            self.add_document(document_id, text, metadata)

    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: dict | None = None,
    ) -> list[RetrievedDocument]:
        query_counts = Counter(clean_text(query).split())
        if not query_counts:
            return []

        scored: list[RetrievedDocument] = []
        for document in self._documents.values():
            if filters and not self._matches_filters(document.metadata, filters):
                continue

            score = self._cosine(query_counts, document.term_counts)
            keyword_overlap = len(set(query_counts).intersection(document.term_counts))
            combined_score = score + (0.05 * keyword_overlap)
            if combined_score > 0:
                scored.append(
                    RetrievedDocument(
                        document_id=document.document_id,
                        text=document.text,
                        score=round(combined_score, 5),
                        metadata=document.metadata,
                    )
                )

        return sorted(scored, key=lambda doc: doc.score, reverse=True)[:top_k]

    @staticmethod
    def _matches_filters(metadata: dict, filters: dict) -> bool:
        for key, expected in filters.items():
            actual = metadata.get(key)
            if isinstance(expected, (set, list, tuple)):
                if actual not in expected:
                    return False
            elif actual != expected:
                return False
        return True

    @staticmethod
    def _cosine(left: Counter[str], right: Counter[str]) -> float:
        shared = set(left).intersection(right)
        numerator = sum(left[token] * right[token] for token in shared)
        left_norm = sqrt(sum(value * value for value in left.values()))
        right_norm = sqrt(sum(value * value for value in right.values()))
        if not left_norm or not right_norm:
            return 0.0
        return numerator / (left_norm * right_norm)
