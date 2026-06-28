"""Deterministic event intelligence workflow.

This workflow gives the repo a working multi-agent spine without requiring LLM
keys. In production, each method maps cleanly to a LangGraph node backed by an
LLM and tool-calling policy.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from packages.schemas import AgentDecision, CandidateEvent, Citation, EvidenceItem, Report
from services.memory import MemoryRecord, MemoryStore
from services.retrieval import HybridRetriever
from services.tools import ToolGateway


@dataclass(frozen=True)
class WorkflowResult:
    event: CandidateEvent
    decisions: tuple[AgentDecision, ...]
    evidence: tuple[EvidenceItem, ...]
    report: Report
    requires_human_review: bool


@dataclass
class EventIntelligenceWorkflow:
    retriever: HybridRetriever
    memory: MemoryStore
    tools: ToolGateway = field(default_factory=ToolGateway)

    def run(self, event: CandidateEvent) -> WorkflowResult:
        research = self._research(event)
        verification, evidence = self._verify(event, research)
        impact = self._impact(event, evidence)
        summary = self._summarize(event, verification, impact)
        reflection = self._reflect(event, verification, summary)
        report = self._report(event, summary, evidence)
        self._write_memory(event, summary, reflection)

        decisions = (research, verification, impact, summary, reflection)
        requires_review = any(decision.requires_human_review for decision in decisions)
        event.status = "verified" if verification.confidence >= 0.65 else "disputed"
        event.confidence = min(decision.confidence for decision in decisions)
        return WorkflowResult(
            event=event,
            decisions=decisions,
            evidence=evidence,
            report=report,
            requires_human_review=requires_review,
        )

    def _research(self, event: CandidateEvent) -> AgentDecision:
        query = " ".join(event.topic.keywords)
        docs = self.retriever.search(query=query, top_k=5)
        citations = tuple(
            Citation(
                source_name=str(doc.metadata.get("source", "local-corpus")),
                url=str(doc.metadata.get("url", f"memory://{doc.document_id}")),
                reliability_score=float(doc.metadata.get("reliability_score", 0.6)),
            )
            for doc in docs
        )
        confidence = min(0.9, 0.45 + (0.1 * len(docs)))
        return AgentDecision(
            agent_name="Research Agent",
            conclusion=f"Found {len(docs)} relevant evidence documents for {event.title}.",
            confidence=confidence,
            citations=citations,
            requires_human_review=len(docs) < 2,
            rationale="Research confidence is based on relevant retrieved evidence count.",
            output={"document_ids": [doc.document_id for doc in docs]},
        )

    def _verify(
        self,
        event: CandidateEvent,
        research: AgentDecision,
    ) -> tuple[AgentDecision, tuple[EvidenceItem, ...]]:
        evidence: list[EvidenceItem] = []
        for citation in research.citations:
            evidence.append(
                EvidenceItem(
                    claim=event.summary,
                    stance="supports",
                    citation=citation,
                    evidence_text=f"Source supports the event topic: {event.topic.label}.",
                    reliability_score=citation.reliability_score,
                )
            )

        average_reliability = (
            sum(item.reliability_score for item in evidence) / len(evidence)
            if evidence
            else 0.0
        )
        confidence = round(min(0.95, 0.25 + average_reliability + (0.05 * len(evidence))), 3)
        return (
            AgentDecision(
                agent_name="Fact Verification Agent",
                conclusion="Event has supporting evidence." if evidence else "Evidence is insufficient.",
                confidence=confidence,
                citations=tuple(item.citation for item in evidence),
                requires_human_review=confidence < 0.65,
                rationale="Verification combines source reliability and evidence diversity.",
                output={"supporting_evidence": len(evidence)},
            ),
            tuple(evidence),
        )

    def _impact(self, event: CandidateEvent, evidence: tuple[EvidenceItem, ...]) -> AgentDecision:
        severity = "high" if event.velocity.anomaly_score >= 3 else event.severity
        confidence = 0.7 if evidence else 0.4
        return AgentDecision(
            agent_name="Business Impact Agent",
            conclusion=(
                f"Potential {severity} impact because the topic is accelerating "
                f"with anomaly score {event.velocity.anomaly_score:.2f}."
            ),
            confidence=confidence,
            citations=tuple(item.citation for item in evidence[:3]),
            requires_human_review=severity in {"high", "critical"} and confidence < 0.75,
            rationale="Impact is estimated from semantic velocity and verified evidence availability.",
            output={"severity": severity, "anomaly_score": event.velocity.anomaly_score},
        )

    def _summarize(
        self,
        event: CandidateEvent,
        verification: AgentDecision,
        impact: AgentDecision,
    ) -> AgentDecision:
        confidence = round((verification.confidence + impact.confidence) / 2, 3)
        return AgentDecision(
            agent_name="Executive Summary Agent",
            conclusion=(
                f"{event.title}. {event.summary} "
                f"{impact.conclusion} Verification confidence: {verification.confidence:.2f}."
            ),
            confidence=confidence,
            citations=verification.citations,
            requires_human_review=confidence < 0.65,
            rationale="Summary confidence averages verification and impact confidence.",
        )

    def _reflect(
        self,
        event: CandidateEvent,
        verification: AgentDecision,
        summary: AgentDecision,
    ) -> AgentDecision:
        has_citations = bool(summary.citations)
        confidence = min(verification.confidence, summary.confidence)
        issues = []
        if not has_citations:
            issues.append("No citations available.")
        if confidence < 0.65:
            issues.append("Confidence below publication threshold.")

        return AgentDecision(
            agent_name="Reflection Agent",
            conclusion="Quality gate passed." if not issues else "Human review recommended.",
            confidence=confidence,
            citations=summary.citations,
            requires_human_review=bool(issues),
            rationale="; ".join(issues) if issues else "Evidence, citations, and confidence are sufficient.",
            output={"issues": issues, "event_id": event.event_id},
        )

    def _report(
        self,
        event: CandidateEvent,
        summary: AgentDecision,
        evidence: tuple[EvidenceItem, ...],
    ) -> Report:
        citations = tuple(item.citation for item in evidence)
        citation_lines = "\n".join(
            f"- {citation.source_name}: {citation.url}" for citation in citations
        )
        markdown = (
            f"# {event.title}\n\n"
            f"## Executive Summary\n\n{summary.conclusion}\n\n"
            f"## Confidence\n\n{summary.confidence:.2f}\n\n"
            f"## Citations\n\n{citation_lines or '- No citations available'}\n"
        )
        return Report(
            title=event.title,
            markdown=markdown,
            citations=citations,
            confidence=summary.confidence,
        )

    def _write_memory(
        self,
        event: CandidateEvent,
        summary: AgentDecision,
        reflection: AgentDecision,
    ) -> None:
        self.memory.write(
            MemoryRecord(
                content=f"{event.title}: {summary.conclusion}",
                memory_type="event_summary",
                confidence=summary.confidence,
                source_id=event.event_id,
                metadata={"event_id": event.event_id, "topic": event.topic.label},
            )
        )
        self.memory.write(
            MemoryRecord(
                content=f"Reflection for {event.title}: {reflection.rationale}",
                memory_type="agent_reflection",
                confidence=reflection.confidence,
                source_id=event.event_id,
                metadata={"event_id": event.event_id},
            )
        )
