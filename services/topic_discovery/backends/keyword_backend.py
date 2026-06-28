"""Keyword-based topic clustering backend (legacy fallback).

This module extracts the original keyword-bucketing logic from the prototype
``TopicDiscoveryEngine`` into a standalone backend that satisfies the
:class:`TopicBackend` protocol.  It requires no ML dependencies and runs
instantly, making it ideal for tests, CI, and offline demos.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from packages.schemas import Article, TopicCluster
from packages.schemas.news_intelligence import new_id
from services.topic_discovery.backends.base import TopicModelSnapshot
from services.topic_discovery.config import TopicDiscoverySettings
from src.preprocessing import clean_text


class KeywordBackend:
    """Zero-dependency keyword clustering backend."""

    def __init__(self, settings: TopicDiscoverySettings | None = None) -> None:
        self._settings = settings or TopicDiscoverySettings(backend="keyword")
        self._clusters: list[TopicCluster] = []
        self._model_version = self._make_version()

    # ── TopicBackend interface ───────────────────────────────────────

    def fit(self, articles: list[Article]) -> list[TopicCluster]:
        self._clusters = self._cluster(articles)
        return self._clusters

    def partial_fit(self, articles: list[Article]) -> list[TopicCluster]:
        # Keyword backend has no incremental state — just re-cluster.
        return self.fit(articles)

    def transform(self, articles: list[Article]) -> list[TopicCluster]:
        return self._cluster(articles)

    def get_topics(self) -> list[TopicCluster]:
        return list(self._clusters)

    def get_model_version(self) -> str:
        return self._model_version

    def save(self, directory: Path) -> TopicModelSnapshot:
        directory.mkdir(parents=True, exist_ok=True)
        meta = {
            "model_version": self._model_version,
            "num_topics": len(self._clusters),
            "clusters": [
                {"label": c.label, "keywords": list(c.keywords)}
                for c in self._clusters
            ],
        }
        path = directory / "keyword_model.json"
        path.write_text(json.dumps(meta, indent=2))
        return TopicModelSnapshot(
            model_version=self._model_version,
            path=path,
            num_topics=len(self._clusters),
            num_documents=sum(len(c.article_ids) for c in self._clusters),
        )

    def load(self, directory: Path) -> None:
        path = directory / "keyword_model.json"
        if path.exists():
            meta = json.loads(path.read_text())
            self._model_version = meta.get("model_version", self._model_version)

    # ── Internal ─────────────────────────────────────────────────────

    def _cluster(self, articles: list[Article]) -> list[TopicCluster]:
        min_size = self._settings.keyword_min_cluster_size
        max_kw = self._settings.keyword_max_keywords

        buckets: dict[str, list[Article]] = defaultdict(list)
        bucket_terms: dict[str, set[str]] = defaultdict(set)
        keyword_counts: dict[str, Counter[str]] = defaultdict(Counter)

        for article in articles:
            tokens = clean_text(article.text).split()
            if not tokens:
                continue

            top_terms = [t for t, _ in Counter(tokens).most_common(10)]
            anchor = self._select_bucket(top_terms, bucket_terms) or top_terms[0]
            buckets[anchor].append(article)
            bucket_terms[anchor].update(top_terms)
            keyword_counts[anchor].update(top_terms)

        clusters: list[TopicCluster] = []
        for anchor, grouped in buckets.items():
            if len(grouped) < min_size:
                continue

            keywords = tuple(t for t, _ in keyword_counts[anchor].most_common(max_kw))
            label = " / ".join(t.title() for t in keywords[:3])
            clusters.append(
                TopicCluster(
                    label=label,
                    keywords=keywords,
                    article_ids=tuple(a.article_id for a in grouped),
                    coherence_score=self._keyword_coherence(grouped, keywords),
                    model_version=self._model_version,
                )
            )

        return sorted(clusters, key=lambda c: len(c.article_ids), reverse=True)

    @staticmethod
    def _select_bucket(
        top_terms: list[str], bucket_terms: dict[str, set[str]]
    ) -> str | None:
        incoming = set(top_terms)
        best_anchor = None
        best_overlap = 0
        for anchor, terms in bucket_terms.items():
            overlap = len(incoming & terms)
            if overlap > best_overlap:
                best_anchor = anchor
                best_overlap = overlap
        return best_anchor if best_overlap >= 1 else None

    @staticmethod
    def _keyword_coherence(
        articles: list[Article], keywords: tuple[str, ...]
    ) -> float:
        if not articles or not keywords:
            return 0.0
        token_sets = [set(clean_text(a.text).split()) for a in articles]
        pair_scores: list[float] = []
        for i, left in enumerate(keywords):
            for right in keywords[i + 1 :]:
                co = sum(1 for ts in token_sets if left in ts and right in ts)
                total = sum(1 for ts in token_sets if left in ts or right in ts)
                if total:
                    pair_scores.append(co / total)
        return round(sum(pair_scores) / len(pair_scores), 4) if pair_scores else 0.0

    def _make_version(self) -> str:
        cfg_hash = hashlib.md5(
            json.dumps(
                {
                    "min_cluster_size": self._settings.keyword_min_cluster_size,
                    "max_keywords": self._settings.keyword_max_keywords,
                },
                sort_keys=True,
            ).encode()
        ).hexdigest()[:8]
        return f"keyword-v1-{cfg_hash}"
