"""Topic discovery service built around the existing NLP research pipeline."""

from .engine import TopicDiscoveryEngine, TopicDiscoveryConfig, compute_semantic_velocity
from .config import TopicDiscoverySettings, BackendType
from .backends.base import TopicBackend, TopicModelSnapshot

__all__ = [
    "TopicDiscoveryEngine",
    "TopicDiscoveryConfig",
    "TopicDiscoverySettings",
    "BackendType",
    "TopicBackend",
    "TopicModelSnapshot",
    "compute_semantic_velocity",
]
