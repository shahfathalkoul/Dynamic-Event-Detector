"""Topic discovery configuration with full BERTopic hyperparameter control.

All settings can be overridden via environment variables with the
``TOPIC_DISCOVERY_`` prefix (e.g. ``TOPIC_DISCOVERY_EMBEDDING_MODEL``).
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class BackendType(str, Enum):
    """Available topic discovery backend implementations."""

    KEYWORD = "keyword"
    BERTOPIC = "bertopic"


class TopicDiscoverySettings(BaseSettings):
    """Central configuration for the topic discovery service."""

    model_config = {"env_prefix": "TOPIC_DISCOVERY_", "case_sensitive": False}

    # ── Backend selection ────────────────────────────────────────────
    backend: BackendType = Field(
        default=BackendType.BERTOPIC,
        description="Which clustering backend to use.",
    )

    # ── Embedding ────────────────────────────────────────────────────
    embedding_model: str = Field(
        default="all-MiniLM-L6-v2",
        description="Sentence-Transformer model name or path.",
    )
    embedding_device: str | None = Field(
        default=None,
        description="Force 'cpu' or 'cuda'. Auto-detected when ``None``.",
    )
    embedding_batch_size: int = Field(
        default=64,
        ge=1,
        description="Batch size for embedding generation.",
    )

    # ── UMAP ─────────────────────────────────────────────────────────
    umap_n_neighbors: int = Field(default=15, ge=2)
    umap_n_components: int = Field(default=5, ge=2)
    umap_min_dist: float = Field(default=0.0, ge=0.0)
    umap_metric: str = Field(default="cosine")
    umap_random_state: int = Field(default=42)

    # ── HDBSCAN ──────────────────────────────────────────────────────
    hdbscan_min_cluster_size: int = Field(default=15, ge=2)
    hdbscan_min_samples: int = Field(default=5, ge=1)
    hdbscan_metric: str = Field(default="euclidean")
    hdbscan_cluster_selection_method: str = Field(default="eom")

    # ── BERTopic ─────────────────────────────────────────────────────
    nr_topics: int | None = Field(
        default=None,
        description="If set, reduce the final number of topics to this value.",
    )
    top_n_words: int = Field(default=10, ge=1)
    min_topic_size: int = Field(default=10, ge=2)
    language: str = Field(default="english")
    calculate_probabilities: bool = Field(default=False)

    # ── Vectorizer (c-TF-IDF) ────────────────────────────────────────
    vectorizer_min_df: int = Field(default=2, ge=1)
    vectorizer_max_df: float = Field(default=0.95, gt=0.0, le=1.0)
    vectorizer_max_features: int | None = Field(default=None)
    vectorizer_ngram_range_min: int = Field(default=1, ge=1)
    vectorizer_ngram_range_max: int = Field(default=2, ge=1)

    # ── Keyword fallback ─────────────────────────────────────────────
    keyword_min_cluster_size: int = Field(default=2, ge=1)
    keyword_max_keywords: int = Field(default=6, ge=1)

    # ── Semantic velocity ────────────────────────────────────────────
    velocity_threshold: float = Field(
        default=1.25,
        description="Anomaly-score threshold to surface a candidate event.",
    )

    # ── Persistence & versioning ─────────────────────────────────────
    model_dir: Path = Field(
        default=Path("data/topic_models"),
        description="Directory for saved BERTopic model snapshots.",
    )
    model_version: str = Field(
        default="auto",
        description="Explicit version tag, or 'auto' for timestamp-based.",
    )

    # ── Batch / incremental processing ───────────────────────────────
    batch_size: int = Field(
        default=1000,
        ge=1,
        description="Number of documents processed per batch.",
    )
    incremental: bool = Field(
        default=False,
        description="Use partial_fit for streaming updates.",
    )

    # ── GPU ───────────────────────────────────────────────────────────
    gpu_enabled: bool = Field(
        default=True,
        description="Allow GPU acceleration when CUDA is available.",
    )
