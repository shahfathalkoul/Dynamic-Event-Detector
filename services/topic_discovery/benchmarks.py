"""Performance benchmarking for topic discovery backends.

Run as a script:

    python -m services.topic_discovery.benchmarks --help

Or import and call ``run_benchmark()`` from tests / notebooks.
"""

from __future__ import annotations

import argparse
import json
import logging
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from packages.schemas import Article
from services.topic_discovery.backends.base import TopicBackend
from services.topic_discovery.backends.keyword_backend import KeywordBackend
from services.topic_discovery.config import BackendType, TopicDiscoverySettings

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Collected metrics from a single benchmark run."""

    backend_name: str
    model_version: str
    num_documents: int
    num_topics: int
    fit_time_seconds: float
    transform_time_seconds: float | None = None
    avg_coherence: float | None = None
    avg_cluster_size: float | None = None
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


def run_benchmark(
    articles: list[Article],
    backend: TopicBackend,
    backend_name: str = "unknown",
    run_transform: bool = True,
) -> BenchmarkResult:
    """Benchmark a single backend on the given articles.

    Parameters
    ----------
    articles:
        The corpus to fit.
    backend:
        An instantiated backend to benchmark.
    backend_name:
        Human-readable name for logging and result labelling.
    run_transform:
        Whether to benchmark ``transform()`` after fitting.
    """
    # ── Fit ───────────────────────────────────────────────────────────
    t0 = time.perf_counter()
    clusters = backend.fit(articles)
    fit_time = time.perf_counter() - t0

    # ── Transform (optional) ─────────────────────────────────────────
    transform_time: float | None = None
    if run_transform and clusters:
        sample = articles[: min(100, len(articles))]
        t1 = time.perf_counter()
        try:
            backend.transform(sample)
            transform_time = time.perf_counter() - t1
        except Exception as exc:
            logger.warning("Transform benchmark skipped: %s", exc)

    # ── Metrics ──────────────────────────────────────────────────────
    coherence_scores = [
        c.coherence_score for c in clusters if c.coherence_score is not None
    ]
    avg_coherence = (
        round(sum(coherence_scores) / len(coherence_scores), 4)
        if coherence_scores
        else None
    )
    avg_size = (
        round(
            sum(len(c.article_ids) for c in clusters) / len(clusters), 1
        )
        if clusters
        else None
    )

    result = BenchmarkResult(
        backend_name=backend_name,
        model_version=backend.get_model_version(),
        num_documents=len(articles),
        num_topics=len(clusters),
        fit_time_seconds=round(fit_time, 3),
        transform_time_seconds=round(transform_time, 3) if transform_time else None,
        avg_coherence=avg_coherence,
        avg_cluster_size=avg_size,
    )
    logger.info(
        "Benchmark [%s]: %d docs → %d topics in %.2fs (coherence=%.4f)",
        backend_name,
        result.num_documents,
        result.num_topics,
        result.fit_time_seconds,
        result.avg_coherence or 0.0,
    )
    return result


def compare_backends(
    articles: list[Article],
    settings: TopicDiscoverySettings | None = None,
) -> list[BenchmarkResult]:
    """Run benchmarks on all available backends and return results."""
    settings = settings or TopicDiscoverySettings()
    results: list[BenchmarkResult] = []

    # Always benchmark keyword backend
    kw_settings = TopicDiscoverySettings(backend=BackendType.KEYWORD)
    kw_backend = KeywordBackend(kw_settings)
    results.append(run_benchmark(articles, kw_backend, "keyword"))

    # Benchmark BERTopic if available
    try:
        from services.topic_discovery.backends.bertopic_backend import (
            BERTopicBackend,
        )

        bt_backend = BERTopicBackend(settings)
        results.append(run_benchmark(articles, bt_backend, "bertopic"))
    except ImportError:
        logger.warning("BERTopic not installed — skipping BERTopic benchmark.")

    return results


def save_results(
    results: list[BenchmarkResult], path: Path | str = "data/benchmark_results.json"
) -> None:
    """Persist benchmark results to a JSON file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    existing: list[dict] = []
    if path.exists():
        existing = json.loads(path.read_text())

    existing.extend(asdict(r) for r in results)
    path.write_text(json.dumps(existing, indent=2))
    logger.info("Benchmark results saved to %s", path)


# ── CLI ──────────────────────────────────────────────────────────────

def _main() -> None:
    parser = argparse.ArgumentParser(description="Topic Discovery Benchmark")
    parser.add_argument("--data", default="data/clean_data.csv", help="Path to CSV data")
    parser.add_argument("--sample", type=int, default=500, help="Number of articles to sample")
    parser.add_argument("--output", default="data/benchmark_results.json", help="Output path")
    args = parser.parse_args()

    import pandas as pd

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    df = pd.read_csv(args.data)
    if args.sample and args.sample < len(df):
        df = df.sample(n=args.sample, random_state=42)

    articles = [
        Article(
            title=row.get("headline", row.get("title", "")),
            body=row.get("short_description", row.get("clean_text", "")),
            source="benchmark",
            category=row.get("category"),
        )
        for _, row in df.iterrows()
    ]

    results = compare_backends(articles)
    save_results(results, args.output)

    print("\n=== Benchmark Results ===")
    for r in results:
        print(
            f"  {r.backend_name:<12} | topics={r.num_topics:<4} | "
            f"fit={r.fit_time_seconds:.2f}s | coherence={r.avg_coherence or 'N/A'}"
        )


if __name__ == "__main__":
    _main()
