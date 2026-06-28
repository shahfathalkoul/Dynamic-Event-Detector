"""Topic discovery and semantic velocity engine.

This module is the production-facing wrapper around the existing research
pipeline. The default implementation is intentionally lightweight so tests and
local demos can run without downloading embedding models. The interfaces are
shaped so a BERTopic/Sentence-BERT/UMAP/HDBSCAN backend can be plugged in
behind the same contract.
"""

from __future__ import annotations

import logging
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from math import log1p
from pathlib import Path

from packages.schemas import Article, CandidateEvent, SemanticVelocitySnapshot, TopicCluster
from packages.schemas.news_intelligence import utc_now
from services.topic_discovery.backends.base import TopicBackend, TopicModelSnapshot
from services.topic_discovery.config import BackendType, TopicDiscoverySettings

logger = logging.getLogger(__name__)


# ── Keep the original dataclass for backward compatibility ───────────
@dataclass(frozen=True)
class TopicDiscoveryConfig:
    min_cluster_size: int = 2
    max_keywords: int = 6
    velocity_threshold: float = 1.25
    model_version: str = "keyword-prototype-v1"


def compute_semantic_velocity(
    current_count: int,
    previous_count: int,
    window_hours: float,
    baseline_count: int | None = None,
) -> tuple[float, float, float]:
    """Compute velocity, acceleration, and anomaly scores for a topic window.

    The production BERTopic pipeline should feed this function article counts
    or weighted cluster membership counts by time window. The log transform
    dampens very large spikes while preserving the early-event signal.
    """
    safe_hours = max(window_hours, 1.0)
    velocity = log1p(current_count) / safe_hours
    previous_velocity = log1p(previous_count) / safe_hours
    acceleration = velocity - previous_velocity

    baseline = previous_count if baseline_count is None else baseline_count
    anomaly = (current_count + 1) / (baseline + 1)
    return velocity, acceleration, anomaly


def _resolve_backend(settings: TopicDiscoverySettings) -> TopicBackend:
    """Instantiate the configured topic-discovery backend."""
    if settings.backend == BackendType.BERTOPIC:
        try:
            from services.topic_discovery.backends.bertopic_backend import (
                BERTopicBackend,
            )

            return BERTopicBackend(settings)
        except ImportError:
            logger.warning(
                "BERTopic dependencies not installed — falling back to keyword backend."
            )

    from services.topic_discovery.backends.keyword_backend import KeywordBackend

    return KeywordBackend(settings)


class TopicDiscoveryEngine:
    """Discover topic clusters and candidate events from article batches.

    The engine delegates clustering to a pluggable :class:`TopicBackend`
    (keyword or BERTopic) and applies semantic-velocity scoring to surface
    candidate events.

    Parameters
    ----------
    settings:
        Full configuration object.  When ``None`` the engine loads defaults
        from environment variables.
    backend:
        Explicit backend instance.  When ``None`` the engine creates one
        from *settings*.
    config:
        Legacy ``TopicDiscoveryConfig`` for backward compatibility with
        existing tests and callers.
    """

    def __init__(
        self,
        settings: TopicDiscoverySettings | None = None,
        backend: TopicBackend | None = None,
        config: TopicDiscoveryConfig | None = None,
    ) -> None:
        # Backward-compat: if the caller passes the old-style config, map it
        if config is not None and settings is None:
            settings = TopicDiscoverySettings(
                backend=BackendType.KEYWORD,
                keyword_min_cluster_size=config.min_cluster_size,
                keyword_max_keywords=config.max_keywords,
                velocity_threshold=config.velocity_threshold,
            )

        self._settings = settings or TopicDiscoverySettings()
        self._backend = backend or _resolve_backend(self._settings)

    # ── Public API (unchanged contract) ──────────────────────────────

    @property
    def backend(self) -> TopicBackend:
        """The active topic-discovery backend."""
        return self._backend

    @property
    def settings(self) -> TopicDiscoverySettings:
        return self._settings

    def discover_topics(self, articles: list[Article]) -> list[TopicCluster]:
        """Group articles into topic clusters using the active backend.

        If the BERTopic backend raises ``ValueError`` (e.g. corpus too small
        for UMAP), the engine automatically falls back to the keyword backend.
        """
        if not articles:
            return []

        try:
            if self._settings.incremental:
                return self._backend.partial_fit(articles)
            return self._backend.fit(articles)
        except ValueError as exc:
            logger.warning(
                "Backend failed (%s) — falling back to keyword backend.", exc
            )
            from services.topic_discovery.backends.keyword_backend import KeywordBackend

            fallback = KeywordBackend(self._settings)
            return fallback.fit(articles)

    def detect_candidate_events(
        self,
        articles: list[Article],
        previous_topic_counts: dict[str, int] | None = None,
        window_start: datetime | None = None,
        window_end: datetime | None = None,
    ) -> list[CandidateEvent]:
        """Detect candidate events from newly discovered topic clusters."""
        previous_topic_counts = previous_topic_counts or {}
        window_end = window_end or max(
            (article.published_at for article in articles), default=utc_now()
        )
        window_start = window_start or (window_end - timedelta(hours=24))
        window_hours = max(
            (window_end - window_start).total_seconds() / 3600, 1.0
        )

        events: list[CandidateEvent] = []
        for cluster in self.discover_topics(articles):
            current_count = len(cluster.article_ids)
            previous_count = previous_topic_counts.get(cluster.label, 0)
            velocity, acceleration, anomaly = compute_semantic_velocity(
                current_count=current_count,
                previous_count=previous_count,
                window_hours=window_hours,
            )
            snapshot = SemanticVelocitySnapshot(
                topic_id=cluster.topic_id,
                window_start=window_start,
                window_end=window_end,
                article_count=current_count,
                velocity_score=velocity,
                acceleration_score=acceleration,
                anomaly_score=anomaly,
            )

            if anomaly >= self._settings.velocity_threshold:
                events.append(
                    CandidateEvent(
                        title=f"Emerging topic: {cluster.label}",
                        topic=cluster,
                        summary=(
                            f"{current_count} articles clustered around "
                            f"{', '.join(cluster.keywords[:4])}."
                        ),
                        velocity=snapshot,
                        confidence=min(0.95, 0.45 + (anomaly / 10)),
                    )
                )

        return events

    # ── Model management ─────────────────────────────────────────────

    def save_model(self, directory: Path | None = None) -> TopicModelSnapshot:
        """Persist the current model to disk."""
        directory = directory or self._settings.model_dir
        return self._backend.save(directory)

    def load_model(self, directory: Path | None = None) -> None:
        """Load a previously saved model."""
        directory = directory or self._settings.model_dir
        self._backend.load(directory)

    def get_model_version(self) -> str:
        """Return the active model version string."""
        return self._backend.get_model_version()
