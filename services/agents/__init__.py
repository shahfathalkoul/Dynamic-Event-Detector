"""Agent workflow package."""

from .workflow import EventIntelligenceWorkflow, WorkflowResult
from .state import WorkflowState, AgentOutput

__all__ = [
    "EventIntelligenceWorkflow",
    "WorkflowResult",
    "WorkflowState",
    "AgentOutput",
]

# LangGraph graph builder is imported lazily
try:
    from .graph import build_graph, run_workflow  # noqa: F401

    __all__.extend(["build_graph", "run_workflow"])
except ImportError:
    pass
