"""Repository protocol and PostgreSQL implementation.

The ``Repository`` protocol defines the contract that both the legacy
``SQLiteRepository`` and the new ``PostgresRepository`` must satisfy.
Application code depends only on the protocol, making the backend
swappable via configuration.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from typing import Any, Protocol, runtime_checkable

from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from packages.schemas import AgentDecision, CandidateEvent, Citation, EvidenceItem, Report
from services.agents import WorkflowResult
from services.storage.models import (
    AgentRunModel,
    AnalystFeedbackModel,
    EventEvidenceModel,
    EventMemoryModel,
    EventModel,
    ReportModel,
    ToolCallModel,
)


# ── Serialization helpers ────────────────────────────────────────────

def _json_safe(value: Any) -> Any:
    """Convert non-JSON-serializable types for JSONB storage."""
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, uuid.UUID):
        return str(value)
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    if isinstance(value, (tuple, frozenset)):
        return list(value)
    return value


def _deep_serialize(obj: Any) -> Any:
    """Recursively convert an object tree to JSON-safe primitives."""
    if isinstance(obj, dict):
        return {k: _deep_serialize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_deep_serialize(v) for v in obj]
    return _json_safe(obj)


# ── Protocol ─────────────────────────────────────────────────────────

@runtime_checkable
class Repository(Protocol):
    """Storage contract shared by SQLite and PostgreSQL adapters."""

    def save_event(self, event: CandidateEvent) -> None: ...
    def save_report(self, event_id: str, report: Report) -> None: ...
    def save_workflow_result(self, result: WorkflowResult) -> None: ...
    def list_events(self, limit: int = 50) -> list[dict]: ...
    def get_event(self, event_id: str) -> dict | None: ...
    def list_reports(self, limit: int = 50) -> list[dict]: ...
    def get_report(self, report_id: str) -> dict | None: ...
    def list_agent_decisions(self, event_id: str) -> list[dict]: ...
    def list_evidence(self, event_id: str) -> list[dict]: ...
    def close(self) -> None: ...


# ── PostgreSQL implementation ────────────────────────────────────────

class PostgresRepository:
    """PostgreSQL-backed repository using SQLAlchemy ORM."""

    def __init__(self, session_factory) -> None:
        self._session_factory = session_factory

    def _session(self) -> Session:
        return self._session_factory()

    # ── Events ───────────────────────────────────────────────────────

    def save_event(self, event: CandidateEvent) -> None:
        with self._session() as session:
            existing = session.get(EventModel, uuid.UUID(event.event_id))
            if existing:
                existing.title = event.title
                existing.status = event.status
                existing.severity = event.severity
                existing.confidence = float(event.confidence)
                existing.summary = event.summary
                existing.entities = _deep_serialize(event.entities)
                existing.geography = _deep_serialize(event.geography)
            else:
                session.add(EventModel(
                    id=uuid.UUID(event.event_id),
                    title=event.title,
                    summary=event.summary,
                    status=event.status,
                    severity=event.severity,
                    confidence=float(event.confidence),
                    entities=_deep_serialize(event.entities),
                    geography=_deep_serialize(event.geography),
                    first_seen_at=event.created_at,
                    last_seen_at=event.created_at,
                ))
            session.commit()

    def list_events(self, limit: int = 50) -> list[dict]:
        with self._session() as session:
            rows = session.execute(
                select(EventModel)
                .order_by(desc(EventModel.updated_at))
                .limit(limit)
            ).scalars().all()
            return [
                {
                    "event_id": str(r.id),
                    "title": r.title,
                    "status": r.status,
                    "severity": r.severity,
                    "confidence": float(r.confidence) if r.confidence else 0.0,
                    "topic_label": "",
                    "created_at": r.created_at.isoformat() if r.created_at else "",
                    "updated_at": r.updated_at.isoformat() if r.updated_at else "",
                }
                for r in rows
            ]

    def get_event(self, event_id: str) -> dict | None:
        with self._session() as session:
            row = session.get(EventModel, uuid.UUID(event_id))
            if row is None:
                return None
            return {
                "event_id": str(row.id),
                "title": row.title,
                "summary": row.summary,
                "status": row.status,
                "severity": row.severity,
                "confidence": float(row.confidence) if row.confidence else 0.0,
                "entities": row.entities or {},
                "geography": row.geography or {},
                "created_at": row.created_at.isoformat() if row.created_at else "",
            }

    # ── Reports ──────────────────────────────────────────────────────

    def save_report(self, event_id: str, report: Report) -> None:
        with self._session() as session:
            existing = session.get(ReportModel, uuid.UUID(report.report_id))
            if existing:
                existing.title = report.title
                existing.content_markdown = report.markdown
                existing.confidence = float(report.confidence)
            else:
                session.add(ReportModel(
                    id=uuid.UUID(report.report_id),
                    report_type="event_analysis",
                    title=report.title,
                    content_markdown=report.markdown,
                    status="draft",
                    confidence=float(report.confidence),
                    event_id=uuid.UUID(event_id),
                    citation_manifest=_deep_serialize(report.citations),
                ))
            session.commit()

    def list_reports(self, limit: int = 50) -> list[dict]:
        with self._session() as session:
            rows = session.execute(
                select(ReportModel)
                .order_by(desc(ReportModel.created_at))
                .limit(limit)
            ).scalars().all()
            return [
                {
                    "report_id": str(r.id),
                    "event_id": str(r.event_id) if r.event_id else "",
                    "title": r.title,
                    "confidence": float(r.confidence) if r.confidence else 0.0,
                    "created_at": r.created_at.isoformat() if r.created_at else "",
                }
                for r in rows
            ]

    def get_report(self, report_id: str) -> dict | None:
        with self._session() as session:
            row = session.get(ReportModel, uuid.UUID(report_id))
            if row is None:
                return None
            return {
                "report_id": str(row.id),
                "title": row.title,
                "markdown": row.content_markdown,
                "confidence": float(row.confidence) if row.confidence else 0.0,
                "citations": row.citation_manifest or [],
                "created_at": row.created_at.isoformat() if row.created_at else "",
            }

    # ── Agent decisions ──────────────────────────────────────────────

    def list_agent_decisions(self, event_id: str) -> list[dict]:
        with self._session() as session:
            rows = session.execute(
                select(AgentRunModel)
                .where(AgentRunModel.event_id == uuid.UUID(event_id))
                .order_by(AgentRunModel.created_at)
            ).scalars().all()
            return [
                {
                    "agent_name": r.agent_name,
                    "status": r.status,
                    "output": r.output_data or {},
                    "latency_ms": r.latency_ms,
                    "created_at": r.created_at.isoformat() if r.created_at else "",
                }
                for r in rows
            ]

    # ── Evidence ─────────────────────────────────────────────────────

    def list_evidence(self, event_id: str) -> list[dict]:
        with self._session() as session:
            rows = session.execute(
                select(EventEvidenceModel)
                .where(EventEvidenceModel.event_id == uuid.UUID(event_id))
                .order_by(EventEvidenceModel.created_at)
            ).scalars().all()
            return [
                {
                    "claim": r.claim,
                    "stance": r.stance,
                    "reliability_score": float(r.reliability_score) if r.reliability_score else 0.0,
                    "evidence_text": r.evidence_text or "",
                }
                for r in rows
            ]

    # ── Workflow results (composite save) ────────────────────────────

    def save_workflow_result(self, result: WorkflowResult) -> None:
        self.save_event(result.event)
        self.save_report(result.event.event_id, result.report)

        with self._session() as session:
            eid = uuid.UUID(result.event.event_id)

            # Clear previous decisions and evidence
            session.query(AgentRunModel).filter(AgentRunModel.event_id == eid).delete()
            session.query(EventEvidenceModel).filter(EventEvidenceModel.event_id == eid).delete()

            for decision in result.decisions:
                session.add(AgentRunModel(
                    event_id=eid,
                    agent_name=decision.agent_name,
                    status="completed",
                    input_data={},
                    output_data=_deep_serialize(asdict(decision)),
                ))

            for item in result.evidence:
                session.add(EventEvidenceModel(
                    event_id=eid,
                    claim=item.claim,
                    stance=item.stance,
                    evidence_text=item.evidence_text,
                    reliability_score=float(item.reliability_score),
                    source_url=item.citation.url if item.citation else None,
                ))

            session.commit()

    # ── Agent runs (new) ─────────────────────────────────────────────

    def save_agent_run(
        self,
        event_id: str,
        agent_name: str,
        status: str,
        input_data: dict,
        output_data: dict | None = None,
        *,
        workflow_id: str | None = None,
        prompt_version: str | None = None,
        model_name: str | None = None,
        latency_ms: int | None = None,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        estimated_cost_usd: float | None = None,
        trace_id: str | None = None,
    ) -> str:
        run_id = uuid.uuid4()
        with self._session() as session:
            session.add(AgentRunModel(
                id=run_id,
                event_id=uuid.UUID(event_id),
                workflow_id=uuid.UUID(workflow_id) if workflow_id else None,
                agent_name=agent_name,
                prompt_version=prompt_version,
                model_name=model_name,
                status=status,
                input_data=_deep_serialize(input_data),
                output_data=_deep_serialize(output_data) if output_data else None,
                latency_ms=latency_ms,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                estimated_cost_usd=estimated_cost_usd,
                trace_id=trace_id,
            ))
            session.commit()
        return str(run_id)

    # ── Tool calls (new) ─────────────────────────────────────────────

    def save_tool_call(
        self,
        agent_run_id: str,
        tool_name: str,
        status: str,
        input_data: dict | None = None,
        output_data: dict | None = None,
        latency_ms: int | None = None,
        error: str | None = None,
    ) -> str:
        call_id = uuid.uuid4()
        with self._session() as session:
            session.add(ToolCallModel(
                id=call_id,
                agent_run_id=uuid.UUID(agent_run_id),
                tool_name=tool_name,
                status=status,
                input_data=_deep_serialize(input_data) if input_data else None,
                output_data=_deep_serialize(output_data) if output_data else None,
                latency_ms=latency_ms,
                error=error,
            ))
            session.commit()
        return str(call_id)

    # ── Feedback (new) ───────────────────────────────────────────────

    def save_feedback(
        self,
        target_type: str,
        target_id: str,
        action: str,
        *,
        analyst_id: str | None = None,
        original_content: dict | None = None,
        corrected_content: dict | None = None,
        feedback_text: str | None = None,
    ) -> str:
        feedback_id = uuid.uuid4()
        with self._session() as session:
            session.add(AnalystFeedbackModel(
                id=feedback_id,
                target_type=target_type,
                target_id=uuid.UUID(target_id),
                analyst_id=uuid.UUID(analyst_id) if analyst_id else None,
                action=action,
                original_content=_deep_serialize(original_content) if original_content else None,
                corrected_content=_deep_serialize(corrected_content) if corrected_content else None,
                feedback_text=feedback_text,
            ))
            session.commit()
        return str(feedback_id)

    def close(self) -> None:
        pass  # Session factory manages lifecycle
