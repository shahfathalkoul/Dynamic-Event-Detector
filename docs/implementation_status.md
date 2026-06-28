# Implementation Status

This document tracks the first concrete upgrade from the original NLP research project into the autonomous News Intelligence Platform.

## Completed in This Milestone

- Added shared domain schemas for articles, topic clusters, semantic velocity snapshots, candidate events, evidence, citations, agent decisions, and reports.
- Wrapped the existing preprocessing and event-detection concepts in `services/topic_discovery/TopicDiscoveryEngine`.
- Added a dependency-light semantic velocity implementation for testable event spike detection.
- Added a local hybrid retriever that models the future BM25 + vector search interface.
- Added searchable long-term memory primitives for event summaries and agent reflections.
- Added a retrying tool gateway that normalizes tool-call success, failures, and missing tools.
- Added a deterministic event intelligence workflow that maps to future LangGraph nodes:
  - Research Agent
  - Fact Verification Agent
  - Business Impact Agent
  - Executive Summary Agent
  - Reflection Agent
  - Memory write step
- Added a FastAPI backend scaffold with:
  - `GET /health`
  - `POST /api/v1/events/detect`
  - `POST /api/v1/events/analyze`
  - `GET /api/v1/events`
  - `GET /api/v1/events/{event_id}`
  - `GET /api/v1/reports`
  - `GET /api/v1/reports/{report_id}`
  - `POST /api/v1/chat/query`
- Added a SQLite persistence adapter for event, evidence, agent decision, workflow result, and report storage.
- Added regression tests using Python `unittest`.
- Updated `requirements.txt` with production backend, workflow, vector DB, queue, cache, and observability dependencies.

## Verification

Run:

```bash
python -m unittest discover -s tests -v
```

Current result:

```text
Ran 8 tests
OK
```

## Next Build Slice

1. Replace the local keyword clustering fallback with a pluggable BERTopic backend that uses Sentence-BERT, UMAP, and HDBSCAN.
2. Promote the SQLite repository boundary to PostgreSQL migrations for events, evidence, agent runs, tool calls, reports, and feedback.
3. Add Qdrant-backed vector retrieval while keeping the current `HybridRetriever` interface.
4. Replace the deterministic workflow internals with LangGraph nodes and structured LLM outputs.
5. Add a Next.js dashboard that consumes the FastAPI routes.
