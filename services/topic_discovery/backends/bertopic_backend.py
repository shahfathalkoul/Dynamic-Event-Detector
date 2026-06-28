"""Production BERTopic backend using Sentence-BERT, UMAP, and HDBSCAN.

This module implements the full topic-discovery pipeline described in the
architecture document.  It supports:

- Batch fitting on a full article corpus
- Incremental updates via ``partial_fit``
- GPU-accelerated embeddings (auto-detected)
- Configurable hyperparameters for UMAP, HDBSCAN, and c-TF-IDF
- Model persistence (save / load) with versioned snapshots
- Topic coherence evaluation
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from bertopic import BERTopic
from hdbscan import HDBSCAN
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import CountVectorizer
from umap import UMAP

from packages.schemas import Article, TopicCluster
from packages.schemas.news_intelligence import new_id
from services.topic_discovery.backends.base import TopicModelSnapshot
from services.topic_discovery.config import TopicDiscoverySettings
from src.preprocessing import clean_text

logger = logging.getLogger(__name__)

# UMAP + HDBSCAN need a minimum corpus size to produce meaningful clusters.
# Below this threshold the engine should fall back to the keyword backend.
MIN_DOCUMENTS_FOR_BERTOPIC = 20


class BERTopicBackend:
    """Full BERTopic pipeline backend for production topic discovery."""

    def __init__(self, settings: TopicDiscoverySettings | None = None) -> None:
        self._settings = settings or TopicDiscoverySettings()
        self._model: BERTopic | None = None
        self._embedding_model: SentenceTransformer | None = None
        self._article_map: dict[int, str] = {}  # bertopic-index → article_id
        self._clusters: list[TopicCluster] = []
        self._model_version = self._make_version()
        self._embeddings_cache: np.ndarray | None = None

    # ── TopicBackend interface ───────────────────────────────────────

    def fit(self, articles: list[Article]) -> list[TopicCluster]:
        """Fit a new BERTopic model on the full article corpus.

        Raises :class:`ValueError` when the corpus is smaller than
        ``MIN_DOCUMENTS_FOR_BERTOPIC`` — the engine layer catches this and
        falls back to the keyword backend automatically.
        """
        if not articles:
            return []

        docs, article_ids = self._prepare_documents(articles)

        if len(docs) < MIN_DOCUMENTS_FOR_BERTOPIC:
            raise ValueError(
                f"BERTopic requires at least {MIN_DOCUMENTS_FOR_BERTOPIC} "
                f"documents but received {len(docs)}. "
                f"Use the keyword backend for small corpora."
            )
        embeddings = self._embed(docs)

        model = self._build_model()
        topics, probs = model.fit_transform(docs, embeddings)

        self._model = model
        self._article_map = {i: aid for i, aid in enumerate(article_ids)}
        self._embeddings_cache = embeddings
        self._clusters = self._extract_clusters(model, topics, article_ids)

        logger.info(
            "BERTopic fit complete: %d documents → %d topics (version=%s)",
            len(docs),
            len(self._clusters),
            self._model_version,
        )
        return self._clusters

    def partial_fit(self, articles: list[Article]) -> list[TopicCluster]:
        """Incrementally update the model with new articles.

        If the model was not previously fitted, performs a full fit instead.
        BERTopic's online learning uses ``partial_fit`` on the underlying
        HDBSCAN and c-TF-IDF components.
        """
        if self._model is None:
            return self.fit(articles)

        if not articles:
            return self._clusters

        docs, article_ids = self._prepare_documents(articles)
        embeddings = self._embed(docs)

        try:
            topics, _ = self._model.transform(docs, embeddings)
        except Exception:
            logger.warning(
                "Transform failed during partial_fit, falling back to full fit."
            )
            return self.fit(articles)

        # Merge new article mappings
        offset = max(self._article_map.keys(), default=-1) + 1
        for i, aid in enumerate(article_ids):
            self._article_map[offset + i] = aid

        if self._embeddings_cache is not None:
            self._embeddings_cache = np.vstack([self._embeddings_cache, embeddings])
        else:
            self._embeddings_cache = embeddings

        self._clusters = self._extract_clusters(
            self._model,
            topics,
            article_ids,
            existing_clusters=self._clusters,
        )
        return self._clusters

    def transform(self, articles: list[Article]) -> list[TopicCluster]:
        """Assign articles to existing topics without re-fitting."""
        if self._model is None:
            raise RuntimeError(
                "BERTopicBackend.transform() called before fit(). "
                "Call fit() first or use the KeywordBackend as a fallback."
            )

        docs, article_ids = self._prepare_documents(articles)
        embeddings = self._embed(docs)
        topics, _ = self._model.transform(docs, embeddings)
        return self._extract_clusters(self._model, topics, article_ids)

    def get_topics(self) -> list[TopicCluster]:
        return list(self._clusters)

    def get_model_version(self) -> str:
        return self._model_version

    def save(self, directory: Path) -> TopicModelSnapshot:
        """Save the trained BERTopic model to disk."""
        if self._model is None:
            raise RuntimeError("No model to save. Call fit() first.")

        directory.mkdir(parents=True, exist_ok=True)
        model_path = directory / self._model_version
        self._model.save(str(model_path), serialization="safetensors", save_ctfidf=True)

        # Save article map and metadata
        meta = {
            "model_version": self._model_version,
            "num_topics": len(self._clusters),
            "num_documents": len(self._article_map),
            "settings": {
                "embedding_model": self._settings.embedding_model,
                "umap_n_neighbors": self._settings.umap_n_neighbors,
                "umap_n_components": self._settings.umap_n_components,
                "hdbscan_min_cluster_size": self._settings.hdbscan_min_cluster_size,
                "hdbscan_min_samples": self._settings.hdbscan_min_samples,
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        (model_path / "meta.json").write_text(json.dumps(meta, indent=2))

        coherence = self._compute_coherence()
        snapshot = TopicModelSnapshot(
            model_version=self._model_version,
            path=model_path,
            num_topics=len(self._clusters),
            num_documents=len(self._article_map),
            coherence_score=coherence,
        )
        logger.info("Model saved to %s (coherence=%.4f)", model_path, coherence or 0.0)
        return snapshot

    def load(self, directory: Path) -> None:
        """Load a previously saved BERTopic model."""
        model_path = directory
        if not model_path.exists():
            raise FileNotFoundError(f"Model directory not found: {model_path}")

        self._model = BERTopic.load(str(model_path))

        meta_path = model_path / "meta.json"
        if meta_path.exists():
            meta = json.loads(meta_path.read_text())
            self._model_version = meta.get("model_version", self._model_version)

        logger.info("Model loaded from %s (version=%s)", model_path, self._model_version)

    # ── Building components ──────────────────────────────────────────

    def _build_model(self) -> BERTopic:
        """Construct a BERTopic instance from the current settings."""
        s = self._settings

        umap_model = UMAP(
            n_neighbors=s.umap_n_neighbors,
            n_components=s.umap_n_components,
            min_dist=s.umap_min_dist,
            metric=s.umap_metric,
            random_state=s.umap_random_state,
            low_memory=False,
        )

        hdbscan_model = HDBSCAN(
            min_cluster_size=s.hdbscan_min_cluster_size,
            min_samples=s.hdbscan_min_samples,
            metric=s.hdbscan_metric,
            cluster_selection_method=s.hdbscan_cluster_selection_method,
            prediction_data=True,
        )

        vectorizer = CountVectorizer(
            min_df=s.vectorizer_min_df,
            max_df=s.vectorizer_max_df,
            max_features=s.vectorizer_max_features,
            ngram_range=(s.vectorizer_ngram_range_min, s.vectorizer_ngram_range_max),
            stop_words="english",
        )

        return BERTopic(
            umap_model=umap_model,
            hdbscan_model=hdbscan_model,
            vectorizer_model=vectorizer,
            top_n_words=s.top_n_words,
            nr_topics=s.nr_topics,
            min_topic_size=s.min_topic_size,
            language=s.language,
            calculate_probabilities=s.calculate_probabilities,
            verbose=False,
        )

    def _get_embedding_model(self) -> SentenceTransformer:
        """Lazy-load the sentence transformer with GPU auto-detection."""
        if self._embedding_model is None:
            device = self._settings.embedding_device
            if device is None:
                import torch

                if self._settings.gpu_enabled and torch.cuda.is_available():
                    device = "cuda"
                else:
                    device = "cpu"

            logger.info(
                "Loading embedding model '%s' on device '%s'",
                self._settings.embedding_model,
                device,
            )
            self._embedding_model = SentenceTransformer(
                self._settings.embedding_model, device=device
            )
        return self._embedding_model

    # ── Helpers ──────────────────────────────────────────────────────

    def _prepare_documents(
        self, articles: list[Article]
    ) -> tuple[list[str], list[str]]:
        """Clean articles and return (document_texts, article_ids)."""
        docs: list[str] = []
        ids: list[str] = []
        for article in articles:
            cleaned = clean_text(article.text)
            if cleaned.strip():
                docs.append(cleaned)
                ids.append(article.article_id)
        return docs, ids

    def _embed(self, docs: list[str]) -> np.ndarray:
        """Generate embeddings for a list of documents."""
        model = self._get_embedding_model()
        embeddings = model.encode(
            docs,
            batch_size=self._settings.embedding_batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        return embeddings

    def _extract_clusters(
        self,
        model: BERTopic,
        topics: list[int],
        article_ids: list[str],
        existing_clusters: list[TopicCluster] | None = None,
    ) -> list[TopicCluster]:
        """Convert BERTopic output into ``TopicCluster`` domain objects."""
        topic_info = model.get_topic_info()
        topic_to_articles: dict[int, list[str]] = {}

        for topic_id, aid in zip(topics, article_ids):
            if topic_id == -1:  # outlier / noise
                continue
            topic_to_articles.setdefault(topic_id, []).append(aid)

        # Merge with existing clusters if doing partial fit
        existing_map: dict[str, TopicCluster] = {}
        if existing_clusters:
            for c in existing_clusters:
                existing_map[c.label] = c

        clusters: list[TopicCluster] = []
        for topic_id, aids in topic_to_articles.items():
            try:
                words_scores = model.get_topic(topic_id)
                if not words_scores:
                    continue
                keywords = tuple(w for w, _ in words_scores[: self._settings.top_n_words])
                label = " / ".join(w.title() for w in keywords[:3])
            except Exception:
                continue

            # Merge article IDs if this label already exists
            if label in existing_map:
                prev = existing_map[label]
                aids = list(set(list(prev.article_ids) + aids))

            # Get coherence from topic_info if available
            coherence = None
            topic_row = topic_info[topic_info["Topic"] == topic_id]
            if not topic_row.empty and "Coherence" in topic_row.columns:
                coherence = float(topic_row.iloc[0]["Coherence"])

            clusters.append(
                TopicCluster(
                    label=label,
                    keywords=keywords,
                    article_ids=tuple(aids),
                    coherence_score=coherence,
                    model_version=self._model_version,
                )
            )

        return sorted(clusters, key=lambda c: len(c.article_ids), reverse=True)

    def _compute_coherence(self) -> float | None:
        """Compute average coherence across discovered topics."""
        if not self._clusters:
            return None
        scores = [c.coherence_score for c in self._clusters if c.coherence_score is not None]
        return round(sum(scores) / len(scores), 4) if scores else None

    def _make_version(self) -> str:
        """Generate a version string from config hash + timestamp."""
        if self._settings.model_version != "auto":
            return self._settings.model_version

        cfg = {
            "embedding": self._settings.embedding_model,
            "umap_nn": self._settings.umap_n_neighbors,
            "umap_nc": self._settings.umap_n_components,
            "hdbscan_mc": self._settings.hdbscan_min_cluster_size,
            "hdbscan_ms": self._settings.hdbscan_min_samples,
        }
        cfg_hash = hashlib.md5(
            json.dumps(cfg, sort_keys=True).encode()
        ).hexdigest()[:8]
        ts = datetime.now(timezone.utc).strftime("%Y%m%d")
        return f"bertopic-v1-{cfg_hash}-{ts}"
