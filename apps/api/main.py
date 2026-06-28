"""FastAPI backend for the autonomous news intelligence platform."""

from __future__ import annotations

from dataclasses import asdict

try:
    from fastapi import FastAPI
except ModuleNotFoundError:  # Keeps imports testable before backend deps are installed.
    FastAPI = None  # type: ignore[assignment]

import logging
from typing import Any
from packages.common.config import PlatformSettings
from packages.schemas import Article
from services.agents import EventIntelligenceWorkflow
from services.memory import MemoryStore
from services.retrieval import HybridRetriever
from services.storage import SQLiteRepository
from services.topic_discovery import TopicDiscoveryEngine

logger = logging.getLogger(__name__)


def _require_fastapi() -> None:
    if FastAPI is None:
        raise RuntimeError(
            "FastAPI is not installed. Run `pip install -r requirements.txt` "
            "before starting the production API."
        )


def create_app(repository: Any | None = None):
    """Create the platform API.

    Supports dynamic injection of production backends (PostgreSQL, Qdrant,
    LangGraph) when running in production environment or configured via env vars.
    """
    _require_fastapi()
    settings = PlatformSettings()
    app = FastAPI(
        title="Autonomous News Intelligence Platform",
        version="1.0.0",
        description="Agentic AI layer around the Dynamic Trend & Event Detector.",
    )

    if repository is None:
        if settings.environment == "production" or settings.database_url.startswith("postgresql"):
            try:
                from services.storage import PostgresRepository, get_engine, make_session_factory
                engine = get_engine(settings.database_url)
                repository = PostgresRepository(make_session_factory(engine))
                logger.info("Connected API to production PostgresRepository")
            except Exception as exc:
                logger.warning("Failed to initialize PostgresRepository (%s), falling back to SQLiteRepository", exc)
                repository = SQLiteRepository()
        else:
            repository = SQLiteRepository()

    if settings.environment == "production" or settings.qdrant_url != "http://localhost:6333":
        try:
            from services.retrieval import QdrantRetriever
            retriever = QdrantRetriever()
            logger.info("Connected API to production QdrantRetriever")
        except Exception as exc:
            logger.warning("Failed to initialize QdrantRetriever (%s), falling back to HybridRetriever", exc)
            retriever = HybridRetriever()
    else:
        retriever = HybridRetriever()

    memory = MemoryStore()
    topic_engine = TopicDiscoveryEngine()

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "service": "news-intelligence-api"}

    @app.post("/api/v1/events/detect")
    def detect_events(payload: dict) -> dict:
        articles = [
            Article(
                title=item.get("title", ""),
                body=item.get("body", item.get("description", "")),
                source=item.get("source", "api"),
                url=item.get("url"),
                category=item.get("category"),
                country=item.get("country"),
            )
            for item in payload.get("articles", [])
        ]

        for article in articles:
            retriever.add_document(
                article.article_id,
                article.text,
                {
                    "source": article.source,
                    "url": article.url or f"article://{article.article_id}",
                    "category": article.category,
                    "country": article.country,
                    "reliability_score": payload.get("default_reliability_score", 0.65),
                },
            )

        events = topic_engine.detect_candidate_events(articles)
        for event in events:
            repository.save_event(event)
        return {"events": [asdict(event) for event in events]}

    @app.get("/api/v1/events")
    def list_events(limit: int = 50) -> dict:
        return {"events": repository.list_events(limit=limit)}

    @app.get("/api/v1/events/{event_id}")
    def get_event(event_id: str) -> dict:
        event = repository.get_event(event_id)
        if event is None:
            return {"status": "not_found", "event": None}
        return {
            "status": "ok",
            "event": event,
            "decisions": repository.list_agent_decisions(event_id),
            "evidence": repository.list_evidence(event_id),
        }

    @app.post("/api/v1/events/analyze")
    def analyze_event(payload: dict) -> dict:
        articles = [
            Article(
                title=item.get("title", ""),
                body=item.get("body", item.get("description", "")),
                source=item.get("source", "api"),
                url=item.get("url"),
            )
            for item in payload.get("articles", [])
        ]
        for article in articles:
            retriever.add_document(
                article.article_id,
                article.text,
                {
                    "source": article.source,
                    "url": article.url or f"article://{article.article_id}",
                    "reliability_score": payload.get("default_reliability_score", 0.65),
                },
            )

        events = topic_engine.detect_candidate_events(articles)
        if not events:
            return {"status": "no_candidate_event", "result": None}

        result = EventIntelligenceWorkflow(retriever, memory).run(events[0])
        repository.save_workflow_result(result)
        return {
            "status": "ok",
            "event": asdict(result.event),
            "decisions": [asdict(decision) for decision in result.decisions],
            "evidence": [asdict(item) for item in result.evidence],
            "report": asdict(result.report),
            "requires_human_review": result.requires_human_review,
        }

    @app.get("/api/v1/reports")
    def list_reports(limit: int = 50) -> dict:
        return {"reports": repository.list_reports(limit=limit)}

    @app.get("/api/v1/reports/{report_id}")
    def get_report(report_id: str) -> dict:
        report = repository.get_report(report_id)
        if report is None:
            return {"status": "not_found", "report": None}
        return {"status": "ok", "report": report}

    @app.post("/api/v1/chat/query")
    def chat_query(payload: dict) -> dict:
        query = payload.get("query", "")
        memories = memory.search(query=query, top_k=payload.get("top_k", 5))
        documents = retriever.search(query=query, top_k=payload.get("top_k", 5))
        return {
            "query": query,
            "retrieved_documents": [asdict(document) for document in documents],
            "retrieved_memories": [asdict(memory_doc) for memory_doc in memories],
        }

    return app


if FastAPI is not None:
    app = create_app()
else:
    app = None
