"""Retrieval utilities for RAG and similar-event search."""

from .hybrid import HybridRetriever, RetrievedDocument
from .embeddings import EmbeddingService, get_embedding_service

__all__ = [
    "HybridRetriever",
    "RetrievedDocument",
    "EmbeddingService",
    "get_embedding_service",
]

# Qdrant retriever is imported lazily to avoid hard dependency
try:
    from .qdrant_retriever import QdrantRetriever, QdrantConfig  # noqa: F401

    __all__.extend(["QdrantRetriever", "QdrantConfig"])
except ImportError:
    pass
