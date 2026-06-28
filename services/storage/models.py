"""SQLAlchemy ORM models for the news intelligence platform.

These models mirror the PostgreSQL schema defined in the architecture
document (Section 4) and are used by both Alembic migrations and the
``PostgresRepository``.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_uuid() -> uuid.UUID:
    return uuid.uuid4()


# ── Portable JSON / UUID types ───────────────────────────────────────
# These fall back gracefully to TEXT / CHAR(36) on SQLite for testing.

from sqlalchemy import TypeDecorator, types


class GUID(TypeDecorator):
    """Platform-independent UUID type: uses PG UUID on Postgres, CHAR(36) elsewhere."""

    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return str(value) if dialect.name != "postgresql" else value
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(value)


class JSONType(TypeDecorator):
    """Platform-independent JSON: uses JSONB on Postgres, TEXT elsewhere."""

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB)
        return dialect.type_descriptor(Text)

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name != "postgresql":
            import json
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, str):
            import json
            return json.loads(value)
        return value


class ArrayType(TypeDecorator):
    """Platform-independent ARRAY: uses PG ARRAY on Postgres, JSON TEXT elsewhere."""

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(ARRAY(Text))
        return dialect.type_descriptor(Text)

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name != "postgresql":
            import json
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, str):
            import json
            return json.loads(value)
        return value


# ── Base ─────────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass


# ── Models ───────────────────────────────────────────────────────────

class SourceModel(Base):
    __tablename__ = "sources"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=_new_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    base_url: Mapped[str | None] = mapped_column(Text)
    credibility_score: Mapped[float] = mapped_column(Numeric(4, 3), default=0.500)
    country: Mapped[str | None] = mapped_column(String(10))
    language: Mapped[str] = mapped_column(String(10), default="en")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    articles = relationship("ArticleModel", back_populates="source")


class ArticleModel(Base):
    __tablename__ = "articles"
    __table_args__ = (
        Index("ix_articles_published_at", "published_at"),
        Index("ix_articles_category", "category"),
        Index("ix_articles_country", "country"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=_new_uuid)
    source_id: Mapped[uuid.UUID | None] = mapped_column(GUID, ForeignKey("sources.id"))
    external_id: Mapped[str | None] = mapped_column(String(255))
    url: Mapped[str | None] = mapped_column(Text, unique=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    body: Mapped[str | None] = mapped_column(Text)
    author: Mapped[str | None] = mapped_column(String(255))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    language: Mapped[str | None] = mapped_column(String(10))
    country: Mapped[str | None] = mapped_column(String(10))
    category: Mapped[str | None] = mapped_column(String(100))
    canonical_hash: Mapped[str | None] = mapped_column(String(64))
    metadata_json: Mapped[dict | None] = mapped_column(JSONType, default=dict)

    source = relationship("SourceModel", back_populates="articles")
    chunks = relationship("ArticleChunkModel", back_populates="article", cascade="all, delete-orphan")


class ArticleChunkModel(Base):
    __tablename__ = "article_chunks"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=_new_uuid)
    article_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer)
    qdrant_point_id: Mapped[uuid.UUID | None] = mapped_column(GUID)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    article = relationship("ArticleModel", back_populates="chunks")


class TopicClusterModel(Base):
    __tablename__ = "topic_clusters"
    __table_args__ = (
        Index("ix_topic_clusters_model_version", "model_version"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=_new_uuid)
    model_version: Mapped[str] = mapped_column(String(100), nullable=False)
    label: Mapped[str | None] = mapped_column(Text)
    keywords: Mapped[list] = mapped_column(ArrayType, nullable=False)
    centroid_qdrant_point_id: Mapped[uuid.UUID | None] = mapped_column(GUID)
    coherence_score: Mapped[float | None] = mapped_column(Numeric(6, 4))
    hdbscan_cluster_id: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    velocity_snapshots = relationship("SemanticVelocitySnapshotModel", back_populates="topic")
    events = relationship("EventModel", back_populates="topic")


class TopicArticleLinkModel(Base):
    __tablename__ = "topic_article_links"

    topic_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("topic_clusters.id", ondelete="CASCADE"), primary_key=True)
    article_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True)
    membership_score: Mapped[float | None] = mapped_column(Numeric(6, 5))


class SemanticVelocitySnapshotModel(Base):
    __tablename__ = "semantic_velocity_snapshots"
    __table_args__ = (
        Index("ix_velocity_topic_window", "topic_id", "window_start", "window_end"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=_new_uuid)
    topic_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("topic_clusters.id"))
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    article_count: Mapped[int] = mapped_column(Integer, nullable=False)
    velocity_score: Mapped[float] = mapped_column(Numeric(10, 5), nullable=False)
    acceleration_score: Mapped[float | None] = mapped_column(Numeric(10, 5))
    baseline_score: Mapped[float | None] = mapped_column(Numeric(10, 5))
    anomaly_score: Mapped[float | None] = mapped_column(Numeric(10, 5))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    topic = relationship("TopicClusterModel", back_populates="velocity_snapshots")


class EventModel(Base):
    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint(
            "status IN ('candidate','researching','verified','disputed','rejected','archived')",
            name="ck_events_status",
        ),
        CheckConstraint(
            "severity IN ('low','medium','high','critical')",
            name="ck_events_severity",
        ),
        Index("ix_events_status", "status"),
        Index("ix_events_severity", "severity"),
        Index("ix_events_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=_new_uuid)
    topic_id: Mapped[uuid.UUID | None] = mapped_column(GUID, ForeignKey("topic_clusters.id"))
    title: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="candidate")
    severity: Mapped[str | None] = mapped_column(String(20))
    confidence: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False, default=0.500)
    first_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    geography: Mapped[dict | None] = mapped_column(JSONType, default=dict)
    entities: Mapped[dict | None] = mapped_column(JSONType, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    topic = relationship("TopicClusterModel", back_populates="events")
    evidence = relationship("EventEvidenceModel", back_populates="event", cascade="all, delete-orphan")
    agent_runs = relationship("AgentRunModel", back_populates="event", cascade="all, delete-orphan")
    memories = relationship("EventMemoryModel", back_populates="event", cascade="all, delete-orphan")


class EventEvidenceModel(Base):
    __tablename__ = "event_evidence"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=_new_uuid)
    event_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    article_id: Mapped[uuid.UUID | None] = mapped_column(GUID, ForeignKey("articles.id"))
    source_url: Mapped[str | None] = mapped_column(Text)
    claim: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_text: Mapped[str | None] = mapped_column(Text)
    evidence_type: Mapped[str | None] = mapped_column(String(50))
    stance: Mapped[str | None] = mapped_column(String(20))
    reliability_score: Mapped[float | None] = mapped_column(Numeric(4, 3))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    event = relationship("EventModel", back_populates="evidence")


class AgentRunModel(Base):
    __tablename__ = "agent_runs"
    __table_args__ = (
        Index("ix_agent_runs_event_id", "event_id"),
        Index("ix_agent_runs_agent_name", "agent_name"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=_new_uuid)
    event_id: Mapped[uuid.UUID | None] = mapped_column(GUID, ForeignKey("events.id"))
    workflow_id: Mapped[uuid.UUID | None] = mapped_column(GUID)
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_version: Mapped[str | None] = mapped_column(String(50))
    model_name: Mapped[str | None] = mapped_column(String(100))
    input_data: Mapped[dict | None] = mapped_column(JSONType)
    output_data: Mapped[dict | None] = mapped_column(JSONType)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    prompt_tokens: Mapped[int | None] = mapped_column(Integer)
    completion_tokens: Mapped[int | None] = mapped_column(Integer)
    estimated_cost_usd: Mapped[float | None] = mapped_column(Numeric(12, 6))
    trace_id: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    event = relationship("EventModel", back_populates="agent_runs")
    tool_calls = relationship("ToolCallModel", back_populates="agent_run", cascade="all, delete-orphan")


class ToolCallModel(Base):
    __tablename__ = "tool_calls"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=_new_uuid)
    agent_run_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False)
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
    input_data: Mapped[dict | None] = mapped_column(JSONType)
    output_data: Mapped[dict | None] = mapped_column(JSONType)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    agent_run = relationship("AgentRunModel", back_populates="tool_calls")


class EventMemoryModel(Base):
    __tablename__ = "event_memories"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=_new_uuid)
    event_id: Mapped[uuid.UUID | None] = mapped_column(GUID, ForeignKey("events.id"))
    memory_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    qdrant_point_id: Mapped[uuid.UUID | None] = mapped_column(GUID)
    confidence: Mapped[float | None] = mapped_column(Numeric(4, 3))
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    valid_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    event = relationship("EventModel", back_populates="memories")


class EventRelationshipModel(Base):
    __tablename__ = "event_relationships"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=_new_uuid)
    source_event_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("events.id"), nullable=False)
    target_event_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("events.id"), nullable=False)
    relation_type: Mapped[str] = mapped_column(String(50), nullable=False)
    strength: Mapped[float | None] = mapped_column(Numeric(4, 3))
    rationale: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ReportModel(Base):
    __tablename__ = "reports"
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft','review','approved','published','rejected')",
            name="ck_reports_status",
        ),
        Index("ix_reports_status", "status"),
        Index("ix_reports_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=_new_uuid)
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    audience: Mapped[str | None] = mapped_column(String(100))
    content_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    citation_manifest: Mapped[dict | None] = mapped_column(JSONType, default=list)
    generated_by_workflow_id: Mapped[uuid.UUID | None] = mapped_column(GUID)
    event_id: Mapped[uuid.UUID | None] = mapped_column(GUID, ForeignKey("events.id"))
    confidence: Mapped[float | None] = mapped_column(Numeric(4, 3))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AnalystFeedbackModel(Base):
    __tablename__ = "analyst_feedback"
    __table_args__ = (
        CheckConstraint(
            "action IN ('approve','reject','edit','correct','label','comment')",
            name="ck_feedback_action",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=_new_uuid)
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_id: Mapped[uuid.UUID] = mapped_column(GUID, nullable=False)
    analyst_id: Mapped[uuid.UUID | None] = mapped_column(GUID)
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    original_content: Mapped[dict | None] = mapped_column(JSONType)
    corrected_content: Mapped[dict | None] = mapped_column(JSONType)
    feedback_text: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class UserWatchlistModel(Base):
    __tablename__ = "user_watchlists"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=_new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(GUID, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    keywords: Mapped[list | None] = mapped_column(ArrayType)
    entities: Mapped[dict | None] = mapped_column(JSONType, default=dict)
    geographies: Mapped[list | None] = mapped_column(ArrayType)
    industries: Mapped[list | None] = mapped_column(ArrayType)
    min_severity: Mapped[str] = mapped_column(String(20), default="medium")
    channels: Mapped[dict | None] = mapped_column(JSONType, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
