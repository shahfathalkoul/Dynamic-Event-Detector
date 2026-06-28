"""Initial schema — all core platform tables.

Revision ID: 001
Revises: None
Create Date: 2025-01-01 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── sources ──────────────────────────────────────────────────────
    op.create_table(
        "sources",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("base_url", sa.Text),
        sa.Column("credibility_score", sa.Numeric(4, 3), server_default="0.500"),
        sa.Column("country", sa.String(10)),
        sa.Column("language", sa.String(10), server_default="'en'"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── articles ─────────────────────────────────────────────────────
    op.create_table(
        "articles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("source_id", sa.String(36), sa.ForeignKey("sources.id")),
        sa.Column("external_id", sa.String(255)),
        sa.Column("url", sa.Text, unique=True),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("body", sa.Text),
        sa.Column("author", sa.String(255)),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("collected_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("language", sa.String(10)),
        sa.Column("country", sa.String(10)),
        sa.Column("category", sa.String(100)),
        sa.Column("canonical_hash", sa.String(64)),
        sa.Column("metadata_json", sa.Text, server_default="'{}'"),
    )
    op.create_index("ix_articles_published_at", "articles", ["published_at"])
    op.create_index("ix_articles_category", "articles", ["category"])
    op.create_index("ix_articles_country", "articles", ["country"])

    # ── article_chunks ───────────────────────────────────────────────
    op.create_table(
        "article_chunks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("article_id", sa.String(36), sa.ForeignKey("articles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("token_count", sa.Integer),
        sa.Column("qdrant_point_id", sa.String(36)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── topic_clusters ───────────────────────────────────────────────
    op.create_table(
        "topic_clusters",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("model_version", sa.String(100), nullable=False),
        sa.Column("label", sa.Text),
        sa.Column("keywords", sa.Text, nullable=False),  # JSON array
        sa.Column("centroid_qdrant_point_id", sa.String(36)),
        sa.Column("coherence_score", sa.Numeric(6, 4)),
        sa.Column("hdbscan_cluster_id", sa.Integer),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_topic_clusters_model_version", "topic_clusters", ["model_version"])

    # ── topic_article_links ──────────────────────────────────────────
    op.create_table(
        "topic_article_links",
        sa.Column("topic_id", sa.String(36), sa.ForeignKey("topic_clusters.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("article_id", sa.String(36), sa.ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("membership_score", sa.Numeric(6, 5)),
    )

    # ── semantic_velocity_snapshots ──────────────────────────────────
    op.create_table(
        "semantic_velocity_snapshots",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("topic_id", sa.String(36), sa.ForeignKey("topic_clusters.id")),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("window_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("article_count", sa.Integer, nullable=False),
        sa.Column("velocity_score", sa.Numeric(10, 5), nullable=False),
        sa.Column("acceleration_score", sa.Numeric(10, 5)),
        sa.Column("baseline_score", sa.Numeric(10, 5)),
        sa.Column("anomaly_score", sa.Numeric(10, 5)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_velocity_topic_window", "semantic_velocity_snapshots", ["topic_id", "window_start", "window_end"])

    # ── events ───────────────────────────────────────────────────────
    op.create_table(
        "events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("topic_id", sa.String(36), sa.ForeignKey("topic_clusters.id")),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("summary", sa.Text),
        sa.Column("status", sa.String(20), nullable=False, server_default="'candidate'"),
        sa.Column("severity", sa.String(20)),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=False, server_default="0.500"),
        sa.Column("first_seen_at", sa.DateTime(timezone=True)),
        sa.Column("last_seen_at", sa.DateTime(timezone=True)),
        sa.Column("geography", sa.Text, server_default="'{}'"),
        sa.Column("entities", sa.Text, server_default="'{}'"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_events_status", "events", ["status"])
    op.create_index("ix_events_severity", "events", ["severity"])
    op.create_index("ix_events_created_at", "events", ["created_at"])

    # ── event_evidence ───────────────────────────────────────────────
    op.create_table(
        "event_evidence",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("event_id", sa.String(36), sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("article_id", sa.String(36), sa.ForeignKey("articles.id")),
        sa.Column("source_url", sa.Text),
        sa.Column("claim", sa.Text, nullable=False),
        sa.Column("evidence_text", sa.Text),
        sa.Column("evidence_type", sa.String(50)),
        sa.Column("stance", sa.String(20)),
        sa.Column("reliability_score", sa.Numeric(4, 3)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── agent_runs ───────────────────────────────────────────────────
    op.create_table(
        "agent_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("event_id", sa.String(36), sa.ForeignKey("events.id")),
        sa.Column("workflow_id", sa.String(36)),
        sa.Column("agent_name", sa.String(100), nullable=False),
        sa.Column("prompt_version", sa.String(50)),
        sa.Column("model_name", sa.String(100)),
        sa.Column("input_data", sa.Text),
        sa.Column("output_data", sa.Text),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("latency_ms", sa.Integer),
        sa.Column("prompt_tokens", sa.Integer),
        sa.Column("completion_tokens", sa.Integer),
        sa.Column("estimated_cost_usd", sa.Numeric(12, 6)),
        sa.Column("trace_id", sa.String(100)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_agent_runs_event_id", "agent_runs", ["event_id"])
    op.create_index("ix_agent_runs_agent_name", "agent_runs", ["agent_name"])

    # ── tool_calls ───────────────────────────────────────────────────
    op.create_table(
        "tool_calls",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("agent_run_id", sa.String(36), sa.ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tool_name", sa.String(100), nullable=False),
        sa.Column("input_data", sa.Text),
        sa.Column("output_data", sa.Text),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("latency_ms", sa.Integer),
        sa.Column("error", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── event_memories ───────────────────────────────────────────────
    op.create_table(
        "event_memories",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("event_id", sa.String(36), sa.ForeignKey("events.id")),
        sa.Column("memory_type", sa.String(50), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("qdrant_point_id", sa.String(36)),
        sa.Column("confidence", sa.Numeric(4, 3)),
        sa.Column("valid_from", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("valid_to", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── event_relationships ──────────────────────────────────────────
    op.create_table(
        "event_relationships",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("source_event_id", sa.String(36), sa.ForeignKey("events.id"), nullable=False),
        sa.Column("target_event_id", sa.String(36), sa.ForeignKey("events.id"), nullable=False),
        sa.Column("relation_type", sa.String(50), nullable=False),
        sa.Column("strength", sa.Numeric(4, 3)),
        sa.Column("rationale", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── reports ──────────────────────────────────────────────────────
    op.create_table(
        "reports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("report_type", sa.String(50), nullable=False),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("audience", sa.String(100)),
        sa.Column("content_markdown", sa.Text, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="'draft'"),
        sa.Column("citation_manifest", sa.Text, server_default="'[]'"),
        sa.Column("generated_by_workflow_id", sa.String(36)),
        sa.Column("event_id", sa.String(36), sa.ForeignKey("events.id")),
        sa.Column("confidence", sa.Numeric(4, 3)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("published_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_reports_status", "reports", ["status"])
    op.create_index("ix_reports_created_at", "reports", ["created_at"])

    # ── analyst_feedback ─────────────────────────────────────────────
    op.create_table(
        "analyst_feedback",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("target_type", sa.String(50), nullable=False),
        sa.Column("target_id", sa.String(36), nullable=False),
        sa.Column("analyst_id", sa.String(36)),
        sa.Column("action", sa.String(20), nullable=False),
        sa.Column("original_content", sa.Text),
        sa.Column("corrected_content", sa.Text),
        sa.Column("feedback_text", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── user_watchlists ──────────────────────────────────────────────
    op.create_table(
        "user_watchlists",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("keywords", sa.Text),
        sa.Column("entities", sa.Text, server_default="'{}'"),
        sa.Column("geographies", sa.Text),
        sa.Column("industries", sa.Text),
        sa.Column("min_severity", sa.String(20), server_default="'medium'"),
        sa.Column("channels", sa.Text, server_default="'{}'"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("user_watchlists")
    op.drop_table("analyst_feedback")
    op.drop_table("reports")
    op.drop_table("event_relationships")
    op.drop_table("event_memories")
    op.drop_table("tool_calls")
    op.drop_table("agent_runs")
    op.drop_table("event_evidence")
    op.drop_table("events")
    op.drop_table("semantic_velocity_snapshots")
    op.drop_table("topic_article_links")
    op.drop_table("topic_clusters")
    op.drop_table("article_chunks")
    op.drop_table("articles")
    op.drop_table("sources")
