"""Qdrant vector retrieval backend.

Replaces the in-memory cosine-similarity retriever with Qdrant for
production-grade vector search with metadata filtering, hybrid
retrieval, and multi-collection support.
"""

from __future__ import annotations

import logging
import os
import uuid
from dataclasses import dataclass, field
from typing import Any

from services.retrieval.embeddings import EmbeddingService, get_embedding_service
from services.retrieval.hybrid import RetrievedDocument

logger = logging.getLogger(__name__)


# ── Configuration ────────────────────────────────────────────────────

@dataclass
class QdrantConfig:
    """Qdrant connection and collection settings."""

    url: str = field(default_factory=lambda: os.environ.get("QDRANT_URL", "http://localhost:6333"))
    api_key: str | None = field(default_factory=lambda: os.environ.get("QDRANT_API_KEY"))
    timeout: float = 30.0
    embedding_model: str = "all-MiniLM-L6-v2"
    default_collection: str = "article_chunks"
    batch_size: int = 100

    # Collection definitions
    COLLECTIONS: dict[str, dict] = field(default_factory=lambda: {
        "article_chunks": {
            "description": "News article text chunks with source metadata",
            "payload_fields": ["article_id", "source_id", "published_at", "title", "url", "country", "category"],
        },
        "event_summaries": {
            "description": "Verified event summaries",
            "payload_fields": ["event_id", "status", "confidence", "severity", "first_seen_at"],
        },
        "reports": {
            "description": "Generated report sections",
            "payload_fields": ["report_id", "report_type", "published_at"],
        },
        "agent_memory": {
            "description": "Agent observation and feedback memory",
            "payload_fields": ["event_id", "memory_type", "confidence"],
        },
        "analyst_corrections": {
            "description": "Analyst corrections and approved edits",
            "payload_fields": ["feedback_id", "target_type", "action"],
        },
    })


class QdrantRetriever:
    """Production vector retriever backed by Qdrant.

    Provides the same ``search()`` interface as ``HybridRetriever`` for
    backward compatibility, plus additional methods for multi-collection
    search, batch indexing, and metadata filtering.
    """

    def __init__(
        self,
        config: QdrantConfig | None = None,
        embedding_service: EmbeddingService | None = None,
    ) -> None:
        self._config = config or QdrantConfig()
        self._embeddings = embedding_service or get_embedding_service(
            self._config.embedding_model
        )
        self._client = None

    @property
    def client(self):
        """Lazy-load the Qdrant client."""
        if self._client is None:
            from qdrant_client import QdrantClient

            self._client = QdrantClient(
                url=self._config.url,
                api_key=self._config.api_key,
                timeout=self._config.timeout,
            )
            self._ensure_collections()
        return self._client

    # ── Collection management ────────────────────────────────────────

    def _ensure_collections(self) -> None:
        """Create collections if they don't exist."""
        from qdrant_client.models import Distance, VectorParams

        existing = {c.name for c in self._client.get_collections().collections}
        dimension = self._embeddings.dimension

        for name in self._config.COLLECTIONS:
            if name not in existing:
                self._client.create_collection(
                    collection_name=name,
                    vectors_config=VectorParams(
                        size=dimension,
                        distance=Distance.COSINE,
                    ),
                )
                logger.info("Created Qdrant collection '%s' (dim=%d)", name, dimension)

    def health_check(self) -> bool:
        """Verify Qdrant connectivity."""
        try:
            self.client.get_collections()
            return True
        except Exception as exc:
            logger.error("Qdrant health check failed: %s", exc)
            return False

    # ── Indexing ─────────────────────────────────────────────────────

    def add_document(
        self,
        document_id: str,
        text: str,
        metadata: dict | None = None,
        collection: str | None = None,
    ) -> None:
        """Index a single document."""
        self.add_documents(
            [(document_id, text, metadata or {})],
            collection=collection,
        )

    def add_documents(
        self,
        documents: list[tuple[str, str, dict]],
        collection: str | None = None,
    ) -> None:
        """Batch-index documents into a Qdrant collection."""
        from qdrant_client.models import PointStruct

        collection = collection or self._config.default_collection
        batch_size = self._config.batch_size

        for i in range(0, len(documents), batch_size):
            batch = documents[i: i + batch_size]
            texts = [text for _, text, _ in batch]
            embeddings = self._embeddings.encode(texts)

            points = []
            for (doc_id, text, meta), embedding in zip(batch, embeddings):
                point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, doc_id))
                payload = {
                    "document_id": doc_id,
                    "text": text[:2000],  # Truncate for payload storage
                    "embedding_model": self._embeddings.model_name,
                    **meta,
                }
                points.append(PointStruct(
                    id=point_id,
                    vector=embedding.tolist(),
                    payload=payload,
                ))

            self.client.upsert(collection_name=collection, points=points)

        logger.info(
            "Indexed %d documents into '%s'", len(documents), collection
        )

    # ── Search ───────────────────────────────────────────────────────

    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: dict | None = None,
        collection: str | None = None,
        score_threshold: float | None = None,
    ) -> list[RetrievedDocument]:
        """Search a single collection with optional metadata filters.

        Compatible with the ``HybridRetriever.search()`` interface.
        """
        collection = collection or self._config.default_collection
        query_vector = self._embeddings.encode_single(query)

        # Build Qdrant filter
        qdrant_filter = self._build_filter(filters) if filters else None

        results = self.client.search(
            collection_name=collection,
            query_vector=query_vector.tolist(),
            limit=top_k,
            query_filter=qdrant_filter,
            score_threshold=score_threshold,
        )

        return [
            RetrievedDocument(
                document_id=hit.payload.get("document_id", str(hit.id)),
                text=hit.payload.get("text", ""),
                score=round(hit.score, 5),
                metadata={k: v for k, v in hit.payload.items() if k not in ("text", "document_id")},
            )
            for hit in results
        ]

    def search_multi(
        self,
        query: str,
        collections: list[str] | None = None,
        top_k: int = 5,
        filters: dict | None = None,
    ) -> list[RetrievedDocument]:
        """Search across multiple collections and merge results."""
        collections = collections or list(self._config.COLLECTIONS.keys())
        all_results: list[RetrievedDocument] = []

        for collection in collections:
            try:
                results = self.search(
                    query=query,
                    top_k=top_k,
                    filters=filters,
                    collection=collection,
                )
                for doc in results:
                    doc.metadata["_collection"] = collection
                all_results.extend(results)
            except Exception as exc:
                logger.warning("Search failed for collection '%s': %s", collection, exc)

        # Sort by score and return top_k
        all_results.sort(key=lambda d: d.score, reverse=True)
        return all_results[:top_k]

    # ── Filter building ──────────────────────────────────────────────

    @staticmethod
    def _build_filter(filters: dict) -> Any:
        """Convert a simple dict of filters into Qdrant filter objects."""
        from qdrant_client.models import FieldCondition, Filter, MatchValue, Range

        conditions = []
        for key, value in filters.items():
            if isinstance(value, (list, tuple, set)):
                # Match any value in the list
                for v in value:
                    conditions.append(FieldCondition(key=key, match=MatchValue(value=v)))
            elif isinstance(value, dict) and ("gte" in value or "lte" in value):
                # Range filter
                conditions.append(FieldCondition(
                    key=key,
                    range=Range(
                        gte=value.get("gte"),
                        lte=value.get("lte"),
                    ),
                ))
            else:
                conditions.append(FieldCondition(key=key, match=MatchValue(value=value)))

        return Filter(must=conditions) if conditions else None

    # ── Collection versioning ────────────────────────────────────────

    def create_collection_version(
        self, base_name: str, version_suffix: str
    ) -> str:
        """Create a versioned copy of a collection for reindexing."""
        new_name = f"{base_name}_{version_suffix}"
        from qdrant_client.models import Distance, VectorParams

        self.client.create_collection(
            collection_name=new_name,
            vectors_config=VectorParams(
                size=self._embeddings.dimension,
                distance=Distance.COSINE,
            ),
        )
        logger.info("Created versioned collection '%s'", new_name)
        return new_name

    def add_many(self, documents: list[tuple[str, str, dict]]) -> None:
        """Compatibility method matching HybridRetriever.add_many()."""
        self.add_documents(documents)
