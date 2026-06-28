"""In-memory long-term memory prototype.

This is intentionally small but uses the same primitives the production
PostgreSQL/Qdrant memory service will expose: write observations, search
similar memories, and preserve confidence plus provenance.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from packages.schemas.news_intelligence import new_id, utc_now
from services.retrieval import HybridRetriever, RetrievedDocument


@dataclass(frozen=True)
class MemoryRecord:
    content: str
    memory_type: str
    confidence: float
    source_id: str | None = None
    metadata: dict = field(default_factory=dict)
    memory_id: str = field(default_factory=new_id)
    created_at: object = field(default_factory=utc_now)


class MemoryStore:
    """Searchable memory store for events, forecasts, and analyst feedback."""

    def __init__(self) -> None:
        self._records: dict[str, MemoryRecord] = {}
        self._retriever = HybridRetriever()

    def write(self, record: MemoryRecord) -> MemoryRecord:
        self._records[record.memory_id] = record
        self._retriever.add_document(
            record.memory_id,
            record.content,
            {"memory_type": record.memory_type, **record.metadata},
        )
        return record

    def search(self, query: str, top_k: int = 5, memory_type: str | None = None) -> list[RetrievedDocument]:
        filters = {"memory_type": memory_type} if memory_type else None
        return self._retriever.search(query=query, top_k=top_k, filters=filters)

    def get(self, memory_id: str) -> MemoryRecord | None:
        return self._records.get(memory_id)
