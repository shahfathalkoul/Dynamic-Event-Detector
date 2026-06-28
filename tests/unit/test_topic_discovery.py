"""Unit tests for the refactored topic discovery engine and backends."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from packages.schemas import Article
from services.topic_discovery import (
    TopicDiscoveryEngine,
    TopicDiscoveryConfig,
    TopicDiscoverySettings,
    BackendType,
    compute_semantic_velocity,
)
from services.topic_discovery.backends.keyword_backend import KeywordBackend


def _sample_articles() -> list[Article]:
    """Shared fixture: related articles about AI chip shortages."""
    return [
        Article(
            title="AI chip shortage hits cloud providers",
            body="Semiconductor suppliers report AI accelerator demand and cloud delays.",
        ),
        Article(
            title="Cloud companies face AI semiconductor delays",
            body="AI infrastructure projects depend on chip supply and semiconductor capacity.",
        ),
        Article(
            title="NVIDIA GPU demand exceeds expectations",
            body="AI chip demand pushes semiconductor supply chains to the limit.",
        ),
    ]


class TestSemanticVelocity(unittest.TestCase):
    """Tests for the compute_semantic_velocity function."""

    def test_positive_acceleration(self) -> None:
        v, a, anom = compute_semantic_velocity(10, 2, 24)
        self.assertGreater(v, 0)
        self.assertGreater(a, 0)
        self.assertGreater(anom, 1)

    def test_zero_previous_count(self) -> None:
        v, a, anom = compute_semantic_velocity(5, 0, 12)
        self.assertGreater(v, 0)
        self.assertGreater(anom, 1)

    def test_with_baseline(self) -> None:
        _, _, anom1 = compute_semantic_velocity(10, 2, 24, baseline_count=2)
        _, _, anom2 = compute_semantic_velocity(10, 2, 24, baseline_count=50)
        self.assertGreater(anom1, anom2)

    def test_no_change(self) -> None:
        v, a, anom = compute_semantic_velocity(5, 5, 24)
        self.assertAlmostEqual(a, 0.0)
        self.assertAlmostEqual(anom, 1.0)


class TestTopicDiscoverySettings(unittest.TestCase):
    """Test that settings load with defaults and override properly."""

    def test_default_settings(self) -> None:
        s = TopicDiscoverySettings()
        self.assertEqual(s.backend, BackendType.BERTOPIC)
        self.assertEqual(s.embedding_model, "all-MiniLM-L6-v2")
        self.assertEqual(s.umap_n_neighbors, 15)
        self.assertEqual(s.hdbscan_min_cluster_size, 15)

    def test_keyword_settings(self) -> None:
        s = TopicDiscoverySettings(backend=BackendType.KEYWORD)
        self.assertEqual(s.backend, BackendType.KEYWORD)


class TestKeywordBackend(unittest.TestCase):
    """Tests for the extracted keyword clustering backend."""

    def test_fit_returns_clusters(self) -> None:
        backend = KeywordBackend()
        clusters = backend.fit(_sample_articles())
        self.assertGreaterEqual(len(clusters), 1)
        self.assertTrue(all(len(c.article_ids) >= 1 for c in clusters))

    def test_get_topics_after_fit(self) -> None:
        backend = KeywordBackend()
        backend.fit(_sample_articles())
        topics = backend.get_topics()
        self.assertGreaterEqual(len(topics), 1)

    def test_transform_works(self) -> None:
        backend = KeywordBackend()
        clusters = backend.transform(_sample_articles())
        self.assertGreaterEqual(len(clusters), 1)

    def test_partial_fit_equals_fit(self) -> None:
        backend = KeywordBackend()
        c1 = backend.fit(_sample_articles())
        c2 = backend.partial_fit(_sample_articles())
        self.assertEqual(len(c1), len(c2))

    def test_save_and_load(self) -> None:
        backend = KeywordBackend()
        backend.fit(_sample_articles())
        version = backend.get_model_version()

        with tempfile.TemporaryDirectory() as tmpdir:
            snapshot = backend.save(Path(tmpdir))
            self.assertEqual(snapshot.model_version, version)
            self.assertTrue(snapshot.path.exists())

            new_backend = KeywordBackend()
            new_backend.load(Path(tmpdir))
            self.assertEqual(new_backend.get_model_version(), version)

    def test_model_version_contains_keyword(self) -> None:
        backend = KeywordBackend()
        self.assertIn("keyword", backend.get_model_version())


class TestTopicDiscoveryEngine(unittest.TestCase):
    """Integration tests for the refactored engine with pluggable backends."""

    def test_engine_with_keyword_backend(self) -> None:
        settings = TopicDiscoverySettings(backend=BackendType.KEYWORD)
        engine = TopicDiscoveryEngine(settings=settings)
        clusters = engine.discover_topics(_sample_articles())
        self.assertGreaterEqual(len(clusters), 1)

    def test_backward_compat_legacy_config(self) -> None:
        config = TopicDiscoveryConfig(min_cluster_size=2, max_keywords=4)
        engine = TopicDiscoveryEngine(config=config)
        clusters = engine.discover_topics(_sample_articles())
        self.assertGreaterEqual(len(clusters), 1)

    def test_backward_compat_no_args(self) -> None:
        engine = TopicDiscoveryEngine()
        clusters = engine.discover_topics(_sample_articles())
        self.assertIsInstance(clusters, list)

    def test_detect_candidate_events(self) -> None:
        settings = TopicDiscoverySettings(
            backend=BackendType.KEYWORD,
            keyword_min_cluster_size=2,
        )
        engine = TopicDiscoveryEngine(settings=settings)
        events = engine.detect_candidate_events(_sample_articles())
        self.assertGreaterEqual(len(events), 1)
        self.assertIn("Emerging topic", events[0].title)

    def test_model_version(self) -> None:
        engine = TopicDiscoveryEngine(
            settings=TopicDiscoverySettings(backend=BackendType.KEYWORD)
        )
        version = engine.get_model_version()
        self.assertIn("keyword", version)

    def test_save_and_load_model(self) -> None:
        settings = TopicDiscoverySettings(backend=BackendType.KEYWORD)
        engine = TopicDiscoveryEngine(settings=settings)
        engine.discover_topics(_sample_articles())

        with tempfile.TemporaryDirectory() as tmpdir:
            snapshot = engine.save_model(Path(tmpdir))
            self.assertTrue(snapshot.path.exists())

            engine2 = TopicDiscoveryEngine(settings=settings)
            engine2.load_model(Path(tmpdir))


class TestExistingTestsStillPass(unittest.TestCase):
    """Verify the exact scenarios from the original test suite still work."""

    def test_semantic_velocity_scores_acceleration_and_anomaly(self) -> None:
        velocity, acceleration, anomaly = compute_semantic_velocity(
            current_count=10, previous_count=2, window_hours=24
        )
        self.assertGreater(velocity, 0)
        self.assertGreater(acceleration, 0)
        self.assertGreater(anomaly, 1)

    def test_detect_candidate_event_from_related_articles(self) -> None:
        articles = [
            Article(
                title="AI chip shortage hits cloud providers",
                body="Semiconductor suppliers report AI accelerator demand and cloud delays.",
            ),
            Article(
                title="Cloud companies face AI semiconductor delays",
                body="AI infrastructure projects depend on chip supply and semiconductor capacity.",
            ),
        ]
        events = TopicDiscoveryEngine().detect_candidate_events(articles)
        self.assertEqual(len(events), 1)
        self.assertIn("Emerging topic", events[0].title)
        self.assertGreater(events[0].velocity.anomaly_score, 1)


if __name__ == "__main__":
    unittest.main()
