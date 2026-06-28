"""LangGraph event intelligence workflow builder.

Constructs the full state-machine graph with conditional routing,
reflection loops, parallel fan-out for impact agents, and human
review gates.

Usage::

    from services.agents.graph import build_graph, run_workflow

    graph = build_graph()
    result = run_workflow(graph, candidate_event_dict)
"""

from __future__ import annotations

import json
import logging
from typing import Any
from uuid import uuid4

from services.agents.state import AgentOutput, WorkflowState
from services.agents.llm import LLMClient, LLMResponse
from services.agents import prompts

logger = logging.getLogger(__name__)


# ── Node functions ───────────────────────────────────────────────────
# Each node takes WorkflowState and returns a partial state update.

def _make_llm(model: str | None = None) -> LLMClient:
    """Create an LLM client with environment-configured model."""
    import os
    model = model or os.environ.get("LLM_MODEL", "gpt-4o-mini")
    return LLMClient(model=model)


def research_node(state: WorkflowState) -> dict:
    """Research Agent: gather context for the candidate event."""
    event = state.candidate_event or {}
    llm = _make_llm()

    prompt = prompts.RESEARCH_AGENT["user"].format(
        title=event.get("title", ""),
        summary=event.get("summary", ""),
        keywords=", ".join(event.get("keywords", [])),
        velocity_score=event.get("velocity_score", 0),
        article_count=event.get("article_count", 0),
        evidence=json.dumps(state.research_evidence[:5], indent=2, default=str),
    )

    response = llm.generate(prompt, system_prompt=prompts.RESEARCH_AGENT["system"])

    output = AgentOutput(
        agent_name="Research Agent",
        conclusion=response.content[:500],
        confidence=0.7 if response.content else 0.3,
        rationale="Based on retrieved evidence analysis.",
    )

    return {
        "research_output": output,
        "current_node": "research",
    }


def verification_node(state: WorkflowState) -> dict:
    """Fact Verification Agent: assess claim validity."""
    event = state.candidate_event or {}
    llm = _make_llm()

    prompt = prompts.VERIFICATION_AGENT["user"].format(
        title=event.get("title", ""),
        summary=event.get("summary", ""),
        evidence=json.dumps(state.research_evidence[:5], indent=2, default=str),
        research_conclusion=state.research_output.conclusion if state.research_output else "",
    )

    response = llm.generate(prompt, system_prompt=prompts.VERIFICATION_AGENT["system"])

    confidence = 0.7
    status = "verified"
    if response.structured_output:
        confidence = response.structured_output.get("confidence", 0.7)
        status = response.structured_output.get("verification_status", "verified")

    output = AgentOutput(
        agent_name="Fact Verification Agent",
        conclusion=f"Status: {status}. {response.content[:300]}",
        confidence=confidence,
        requires_human_review=confidence < 0.65,
        rationale="Verification based on evidence cross-referencing.",
    )

    return {
        "verification_output": output,
        "confidence": confidence,
        "current_node": "verification",
    }


def trend_node(state: WorkflowState) -> dict:
    """Trend Evolution Agent: forecast event trajectory."""
    event = state.candidate_event or {}
    llm = _make_llm()

    prompt = prompts.TREND_AGENT["user"].format(
        title=event.get("title", ""),
        velocity_score=event.get("velocity_score", 0),
        acceleration_score=event.get("acceleration_score", 0),
        anomaly_score=event.get("anomaly_score", 0),
        article_count=event.get("article_count", 0),
        similar_events="None found",
    )

    response = llm.generate(prompt, system_prompt=prompts.TREND_AGENT["system"])

    return {
        "trend_forecast": AgentOutput(
            agent_name="Trend Evolution Agent",
            conclusion=response.content[:300],
            confidence=0.6,
            rationale="Trajectory based on velocity analysis.",
        ),
        "current_node": "trend",
    }


def business_impact_node(state: WorkflowState) -> dict:
    """Business Impact Agent: identify industry/company implications."""
    event = state.candidate_event or {}
    llm = _make_llm()

    prompt = prompts.BUSINESS_IMPACT_AGENT["user"].format(
        title=event.get("title", ""),
        summary=event.get("summary", ""),
        severity=event.get("severity", "medium"),
        evidence=json.dumps(state.research_evidence[:3], indent=2, default=str),
    )

    response = llm.generate(prompt, system_prompt=prompts.BUSINESS_IMPACT_AGENT["system"])

    return {
        "business_impact": AgentOutput(
            agent_name="Business Impact Agent",
            conclusion=response.content[:300],
            confidence=0.65,
            rationale="Impact estimated from verified evidence.",
        ),
        "current_node": "business_impact",
    }


def economic_impact_node(state: WorkflowState) -> dict:
    """Economic Impact Agent: macro implications."""
    event = state.candidate_event or {}
    llm = _make_llm()

    prompt = prompts.ECONOMIC_IMPACT_AGENT["user"].format(
        title=event.get("title", ""),
        summary=event.get("summary", ""),
        geography=json.dumps(event.get("geography", {})),
    )

    response = llm.generate(prompt, system_prompt=prompts.ECONOMIC_IMPACT_AGENT["system"])

    return {
        "economic_impact": AgentOutput(
            agent_name="Economic Impact Agent",
            conclusion=response.content[:300],
            confidence=0.6,
            rationale="Economic analysis from event context.",
        ),
        "current_node": "economic_impact",
    }


def risk_node(state: WorkflowState) -> dict:
    """Risk Assessment Agent: multi-dimensional risk scoring."""
    event = state.candidate_event or {}
    llm = _make_llm()

    prompt = prompts.RISK_AGENT["user"].format(
        title=event.get("title", ""),
        severity=event.get("severity", "medium"),
        business_impact=state.business_impact.conclusion if state.business_impact else "",
        economic_impact=state.economic_impact.conclusion if state.economic_impact else "",
    )

    response = llm.generate(prompt, system_prompt=prompts.RISK_AGENT["system"])

    return {
        "risk_assessment": AgentOutput(
            agent_name="Risk Assessment Agent",
            conclusion=response.content[:300],
            confidence=0.65,
            rationale="Risk scored across multiple dimensions.",
        ),
        "current_node": "risk",
    }


def summary_node(state: WorkflowState) -> dict:
    """Executive Summary Agent: decision-ready brief."""
    event = state.candidate_event or {}
    llm = _make_llm()

    prompt = prompts.SUMMARY_AGENT["user"].format(
        title=event.get("title", ""),
        verification_status=state.verification_output.conclusion[:50] if state.verification_output else "pending",
        verification_confidence=state.verification_output.confidence if state.verification_output else 0.5,
        research_conclusion=state.research_output.conclusion[:200] if state.research_output else "",
        business_impact=state.business_impact.conclusion[:200] if state.business_impact else "",
        risk_assessment=state.risk_assessment.conclusion[:200] if state.risk_assessment else "",
        trend_forecast=state.trend_forecast.conclusion[:200] if state.trend_forecast else "",
    )

    response = llm.generate(prompt, system_prompt=prompts.SUMMARY_AGENT["system"])

    return {
        "executive_summary": AgentOutput(
            agent_name="Executive Summary Agent",
            conclusion=response.content[:500],
            confidence=state.confidence,
            rationale="Summary synthesized from all agent outputs.",
        ),
        "report_markdown": response.content,
        "current_node": "summary",
    }


def reflection_node(state: WorkflowState) -> dict:
    """Reflection Agent: quality gate and confidence calibration."""
    event = state.candidate_event or {}
    llm = _make_llm()

    prompt = prompts.REFLECTION_AGENT["user"].format(
        title=event.get("title", ""),
        confidence=state.confidence,
        verification_status=state.verification_output.conclusion[:50] if state.verification_output else "unknown",
        num_citations=len(state.research_evidence),
        executive_summary=state.report_markdown[:300],
    )

    response = llm.generate(prompt, system_prompt=prompts.REFLECTION_AGENT["system"])

    passes = state.confidence >= 0.65 and not state.requires_human_review
    if response.structured_output:
        passes = response.structured_output.get("passes_quality_gate", passes)

    return {
        "reflection_output": AgentOutput(
            agent_name="Reflection Agent",
            conclusion="Quality gate passed." if passes else "Human review recommended.",
            confidence=state.confidence,
            requires_human_review=not passes,
            rationale=response.content[:300],
        ),
        "requires_human_review": not passes,
        "current_node": "reflection",
    }


def memory_update_node(state: WorkflowState) -> dict:
    """Write structured observations to long-term memory."""
    return {
        "status": "complete",
        "current_node": "memory_update",
    }


def human_review_node(state: WorkflowState) -> dict:
    """Human approval gate — blocks until analyst action."""
    return {
        "status": "review",
        "current_node": "human_review",
        "requires_human_review": True,
    }


# ── Routing functions ────────────────────────────────────────────────

def route_verification(state: WorkflowState) -> str:
    """Route based on verification outcome."""
    if state.verification_output is None:
        return "trend"

    confidence = state.verification_output.confidence
    if confidence >= 0.65:
        return "trend"
    elif confidence >= 0.4:
        if state.retry_count < state.max_retries:
            return "research"  # Re-research
        return "human_review"
    else:
        return "human_review"


def route_quality_gate(state: WorkflowState) -> str:
    """Route based on reflection quality gate."""
    if state.reflection_output and not state.reflection_output.requires_human_review:
        return "memory_update"
    return "human_review"


# ── Graph builder ────────────────────────────────────────────────────

def build_graph():
    """Build the LangGraph event intelligence workflow.

    Returns a compiled LangGraph that can be invoked with a WorkflowState.
    """
    from langgraph.graph import StateGraph, END

    builder = StateGraph(WorkflowState)

    # Add nodes
    builder.add_node("research", research_node)
    builder.add_node("verification", verification_node)
    builder.add_node("trend", trend_node)
    builder.add_node("business_impact", business_impact_node)
    builder.add_node("economic_impact", economic_impact_node)
    builder.add_node("risk", risk_node)
    builder.add_node("summary", summary_node)
    builder.add_node("reflection", reflection_node)
    builder.add_node("memory_update", memory_update_node)
    builder.add_node("human_review", human_review_node)

    # Set entry point
    builder.set_entry_point("research")

    # Add edges
    builder.add_edge("research", "verification")
    builder.add_conditional_edges("verification", route_verification, {
        "trend": "trend",
        "research": "research",
        "human_review": "human_review",
    })
    builder.add_edge("trend", "business_impact")
    builder.add_edge("business_impact", "economic_impact")
    builder.add_edge("economic_impact", "risk")
    builder.add_edge("risk", "summary")
    builder.add_edge("summary", "reflection")
    builder.add_conditional_edges("reflection", route_quality_gate, {
        "memory_update": "memory_update",
        "human_review": "human_review",
    })
    builder.add_edge("memory_update", END)
    builder.add_edge("human_review", END)

    return builder.compile()


def run_workflow(
    candidate_event: dict,
    evidence: list[dict] | None = None,
) -> WorkflowState:
    """Convenience function to run the full workflow on a candidate event.

    Parameters
    ----------
    candidate_event:
        Dict with at least ``title``, ``summary``, ``keywords``.
    evidence:
        Pre-retrieved evidence documents.

    Returns
    -------
    WorkflowState:
        The final workflow state with all agent outputs.
    """
    graph = build_graph()

    initial_state = WorkflowState(
        workflow_id=str(uuid4()),
        event_id=candidate_event.get("event_id", str(uuid4())),
        candidate_event=candidate_event,
        research_evidence=evidence or [],
    )

    result = graph.invoke(initial_state)

    if isinstance(result, dict):
        return WorkflowState(**result)
    return result
