"""Core typed records for the news intelligence platform.

The project can later swap these dataclasses for Pydantic models inside the
FastAPI boundary, but dataclasses keep the domain layer dependency-light and
easy to test in the current research environment.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4


EventStatus = Literal["candidate", "researching", "verified", "disputed", "rejected"]
Severity = Literal["low", "medium", "high", "critical"]
Stance = Literal["supports", "contradicts", "unclear"]


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


def new_id() -> str:
    """Return a sortable-enough unique string for local prototypes and tests."""
    return str(uuid4())


@dataclass(frozen=True)
class Citation:
    source_name: str
    url: str
    published_at: datetime | None = None
    reliability_score: float = 0.5


@dataclass(frozen=True)
class Article:
    title: str
    body: str
    source: str = "unknown"
    url: str | None = None
    published_at: datetime = field(default_factory=utc_now)
    category: str | None = None
    country: str | None = None
    article_id: str = field(default_factory=new_id)

    @property
    def text(self) -> str:
        return f"{self.title}. {self.body}".strip()


@dataclass(frozen=True)
class TopicCluster:
    label: str
    keywords: tuple[str, ...]
    article_ids: tuple[str, ...]
    coherence_score: float | None = None
    model_version: str = "prototype-topic-discovery-v1"
    topic_id: str = field(default_factory=new_id)


@dataclass(frozen=True)
class SemanticVelocitySnapshot:
    topic_id: str
    window_start: datetime
    window_end: datetime
    article_count: int
    velocity_score: float
    acceleration_score: float = 0.0
    anomaly_score: float = 0.0


@dataclass
class CandidateEvent:
    title: str
    topic: TopicCluster
    summary: str
    velocity: SemanticVelocitySnapshot
    status: EventStatus = "candidate"
    severity: Severity = "medium"
    confidence: float = 0.5
    event_id: str = field(default_factory=new_id)
    created_at: datetime = field(default_factory=utc_now)
    entities: dict[str, list[str]] = field(default_factory=dict)
    geography: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class EvidenceItem:
    claim: str
    stance: Stance
    citation: Citation
    evidence_text: str
    reliability_score: float = 0.5


@dataclass(frozen=True)
class AgentDecision:
    agent_name: str
    conclusion: str
    confidence: float
    citations: tuple[Citation, ...] = ()
    requires_human_review: bool = False
    rationale: str = ""
    output: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Report:
    title: str
    markdown: str
    citations: tuple[Citation, ...]
    confidence: float
    report_id: str = field(default_factory=new_id)
    created_at: datetime = field(default_factory=utc_now)
