from __future__ import annotations

import logging
import unittest
import warnings

warnings.filterwarnings(
    "ignore",
    message="Using `httpx` with `starlette.testclient` is deprecated.*",
)
logging.getLogger("httpx").setLevel(logging.WARNING)

from fastapi.testclient import TestClient

from apps.api.main import create_app
from packages.schemas import Article
from services.agents import EventIntelligenceWorkflow
from services.memory import MemoryRecord, MemoryStore
from services.retrieval import HybridRetriever
from services.storage import SQLiteRepository
from services.topic_discovery import TopicDiscoveryEngine, compute_semantic_velocity
from services.tools import ToolGateway


class TopicDiscoveryTests(unittest.TestCase):
    def test_semantic_velocity_scores_acceleration_and_anomaly(self) -> None:
        velocity, acceleration, anomaly = compute_semantic_velocity(
            current_count=10,
            previous_count=2,
            window_hours=24,
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


class RetrievalAndMemoryTests(unittest.TestCase):
    def test_hybrid_retriever_returns_relevant_documents(self) -> None:
        retriever = HybridRetriever()
        retriever.add_document(
            "doc-1",
            "Semiconductor demand rises as AI cloud infrastructure expands.",
            {"source": "Market Wire", "country": "US"},
        )
        retriever.add_document(
            "doc-2",
            "Sports league announces playoff schedule.",
            {"source": "Sports Desk", "country": "US"},
        )

        results = retriever.search("AI semiconductor infrastructure", top_k=1)

        self.assertEqual(results[0].document_id, "doc-1")
        self.assertGreater(results[0].score, 0)

    def test_memory_store_searches_written_records(self) -> None:
        store = MemoryStore()
        store.write(
            MemoryRecord(
                content="AI chip supply event affected cloud infrastructure spending.",
                memory_type="event_summary",
                confidence=0.8,
            )
        )

        results = store.search("cloud chip infrastructure", memory_type="event_summary")

        self.assertEqual(len(results), 1)
        self.assertIn("chip", results[0].text)


class ToolGatewayTests(unittest.TestCase):
    def test_tool_gateway_retries_then_succeeds(self) -> None:
        gateway = ToolGateway(max_attempts=2)
        calls = {"count": 0}

        def flaky_tool(payload: dict) -> dict:
            calls["count"] += 1
            if calls["count"] == 1:
                raise RuntimeError("temporary failure")
            return {"echo": payload["value"]}

        gateway.register("flaky.echo", flaky_tool)

        result = gateway.call("flaky.echo", {"value": "ok"})

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.attempts, 2)
        self.assertEqual(result.output["echo"], "ok")


class WorkflowTests(unittest.TestCase):
    def _run_demo_workflow(self) -> tuple[object, MemoryStore]:
        articles = [
            Article(
                title="AI chip shortage hits cloud providers",
                body="Semiconductor suppliers report AI accelerator demand and cloud delays.",
                source="Demo News",
                url="https://example.com/a",
            ),
            Article(
                title="Cloud companies face AI semiconductor delays",
                body="AI infrastructure projects depend on chip supply and semiconductor capacity.",
                source="Market Wire",
                url="https://example.com/b",
            ),
        ]
        event = TopicDiscoveryEngine().detect_candidate_events(articles)[0]
        retriever = HybridRetriever()
        for article in articles:
            retriever.add_document(
                article.article_id,
                article.text,
                {
                    "source": article.source,
                    "url": article.url,
                    "reliability_score": 0.8,
                },
            )

        memory = MemoryStore()
        result = EventIntelligenceWorkflow(retriever, memory).run(event)
        return result, memory

    def test_event_workflow_generates_report_and_memory(self) -> None:
        result, memory = self._run_demo_workflow()

        self.assertEqual(result.event.status, "verified")
        self.assertEqual(len(result.evidence), 2)
        self.assertIn("Executive Summary", result.report.markdown)
        self.assertGreaterEqual(len(memory.search("AI chip cloud")), 1)

    def test_sqlite_repository_persists_workflow_result(self) -> None:
        result, _ = self._run_demo_workflow()
        repository = SQLiteRepository(":memory:")

        repository.save_workflow_result(result)

        events = repository.list_events()
        reports = repository.list_reports()
        stored_event = repository.get_event(result.event.event_id)
        decisions = repository.list_agent_decisions(result.event.event_id)
        evidence = repository.list_evidence(result.event.event_id)

        self.assertEqual(len(events), 1)
        self.assertEqual(len(reports), 1)
        self.assertEqual(stored_event["event_id"], result.event.event_id)
        self.assertEqual(len(decisions), 5)
        self.assertEqual(len(evidence), 2)


class ApiTests(unittest.TestCase):
    def test_api_analyzes_and_persists_event(self) -> None:
        repository = SQLiteRepository(":memory:")
        client = TestClient(create_app(repository=repository))

        response = client.post(
            "/api/v1/events/analyze",
            json={
                "default_reliability_score": 0.8,
                "articles": [
                    {
                        "title": "AI chip shortage hits cloud providers",
                        "body": "Semiconductor suppliers report AI accelerator demand and cloud delays.",
                        "source": "Demo News",
                        "url": "https://example.com/a",
                    },
                    {
                        "title": "Cloud companies face AI semiconductor delays",
                        "body": "AI infrastructure projects depend on chip supply and semiconductor capacity.",
                        "source": "Market Wire",
                        "url": "https://example.com/b",
                    },
                ],
            },
        )

        payload = response.json()
        event_id = payload["event"]["event_id"]
        report_id = payload["report"]["report_id"]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(len(client.get("/api/v1/events").json()["events"]), 1)
        self.assertEqual(client.get(f"/api/v1/events/{event_id}").json()["status"], "ok")
        self.assertEqual(len(client.get("/api/v1/reports").json()["reports"]), 1)
        self.assertEqual(client.get(f"/api/v1/reports/{report_id}").json()["status"], "ok")


if __name__ == "__main__":
    unittest.main()
