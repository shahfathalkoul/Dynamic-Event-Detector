"""Pluggable topic-discovery backends."""

from .base import TopicBackend
from .keyword_backend import KeywordBackend

__all__ = ["TopicBackend", "KeywordBackend"]

# BERTopicBackend is imported lazily to avoid hard dependency on torch/bertopic
# when running in lightweight test or CI environments.
try:
    from .bertopic_backend import BERTopicBackend  # noqa: F401

    __all__.append("BERTopicBackend")
except ImportError:
    pass
