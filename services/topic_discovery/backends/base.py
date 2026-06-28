"""Abstract protocol for topic-discovery backends.

Every backend must implement this interface so the ``TopicDiscoveryEngine``
can swap implementations at runtime without touching the rest of the
service layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, runtime_checkable

from packages.schemas import Article, TopicCluster


@dataclass(frozen=True)
class TopicModelSnapshot:
    """Metadata about a persisted model checkpoint."""

    model_version: str
    path: Path
    num_topics: int
    num_documents: int
    coherence_score: float | None = None
    extra: dict = field(default_factory=dict)


@runtime_checkable
class TopicBackend(Protocol):
    """Contract that every topic-discovery backend must satisfy."""

    # ── Fitting ──────────────────────────────────────────────────────

    def fit(self, articles: list[Article]) -> list[TopicCluster]:
        """Fit the model on a full article corpus and return clusters."""
        ...

    def partial_fit(self, articles: list[Article]) -> list[TopicCluster]:
        """Incrementally update the model with new articles.

        Backends that do not support incremental learning should fall back
        to a full ``fit`` call.
        """
        ...

    # ── Inference ────────────────────────────────────────────────────

    def transform(self, articles: list[Article]) -> list[TopicCluster]:
        """Assign articles to existing clusters without re-fitting."""
        ...

    # ── Introspection ────────────────────────────────────────────────

    def get_topics(self) -> list[TopicCluster]:
        """Return the current set of discovered topic clusters."""
        ...

    def get_model_version(self) -> str:
        """Return the human-readable model version string."""
        ...

    # ── Persistence ──────────────────────────────────────────────────

    def save(self, directory: Path) -> TopicModelSnapshot:
        """Persist the trained model to *directory*."""
        ...

    def load(self, directory: Path) -> None:
        """Restore a previously saved model from *directory*."""
        ...
