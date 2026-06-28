"""LangGraph workflow state model.

Typed state that flows through the event intelligence graph.
All intermediate results are captured here for persistence,
observability, and human review.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal
from pydantic import BaseModel, Field
from operator import add


class AgentOutput(BaseModel):
    """Standardized output from any agent node."""
    agent_name: str
    conclusion: str = ""
    confidence: float = 0.5
    citations: list[dict] = Field(default_factory=list)
    requires_human_review: bool = False
    rationale: str = ""
    output: dict = Field(default_factory=dict)


class WorkflowState(BaseModel):
    """Full state for the event intelligence LangGraph workflow."""

    # ── Identity ─────────────────────────────────────────────────────
    workflow_id: str = ""
    event_id: str | None = None
    topic_id: str | None = None

    # ── Input ────────────────────────────────────────────────────────
    candidate_event: dict | None = None
    articles: list[dict] = Field(default_factory=list)

    # ── Agent outputs ────────────────────────────────────────────────
    research_output: AgentOutput | None = None
    verification_output: AgentOutput | None = None
    trend_forecast: AgentOutput | None = None
    business_impact: AgentOutput | None = None
    economic_impact: AgentOutput | None = None
    risk_assessment: AgentOutput | None = None
    executive_summary: AgentOutput | None = None
    reflection_output: AgentOutput | None = None

    # ── Evidence ─────────────────────────────────────────────────────
    research_evidence: list[dict] = Field(default_factory=list)
    verified_claims: list[dict] = Field(default_factory=list)
    disputed_claims: list[dict] = Field(default_factory=list)

    # ── Control flow ─────────────────────────────────────────────────
    confidence: float = 0.5
    requires_human_review: bool = False
    status: Literal["running", "blocked", "review", "complete", "failed"] = "running"
    current_node: str = ""
    retry_count: int = 0
    max_retries: int = 2
    errors: list[str] = Field(default_factory=list)

    # ── Report ───────────────────────────────────────────────────────
    report: dict | None = None
    report_markdown: str = ""

    # ── Messages (for LangGraph message passing) ─────────────────────
    messages: list[dict] = Field(default_factory=list)
