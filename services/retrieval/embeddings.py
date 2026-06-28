"""Shared embedding service for topic discovery and retrieval.

Provides a unified interface for generating embeddings across the platform,
with lazy model loading, GPU support, and batch encoding.
"""

from __future__ import annotations

import logging
from functools import lru_cache

import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Generate embeddings using Sentence-Transformers.

    The model is loaded lazily on first use and cached for the lifetime
    of the instance.
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        device: str | None = None,
        batch_size: int = 64,
    ) -> None:
        self._model_name = model_name
        self._device = device
        self._batch_size = batch_size
        self._model = None

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        """Return the embedding dimension for the loaded model."""
        model = self._get_model()
        return model.get_sentence_embedding_dimension()

    def encode(
        self,
        texts: list[str],
        batch_size: int | None = None,
        show_progress: bool = False,
    ) -> np.ndarray:
        """Encode a list of texts into embeddings."""
        if not texts:
            return np.array([])

        model = self._get_model()
        return model.encode(
            texts,
            batch_size=batch_size or self._batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

    def encode_single(self, text: str) -> np.ndarray:
        """Encode a single text and return a 1-D vector."""
        result = self.encode([text])
        return result[0]

    def _get_model(self):
        """Lazy-load the SentenceTransformer model."""
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            device = self._device
            if device is None:
                try:
                    import torch
                    device = "cuda" if torch.cuda.is_available() else "cpu"
                except ImportError:
                    device = "cpu"

            logger.info("Loading embedding model '%s' on '%s'", self._model_name, device)
            self._model = SentenceTransformer(self._model_name, device=device)
        return self._model


@lru_cache(maxsize=4)
def get_embedding_service(
    model_name: str = "all-MiniLM-L6-v2",
    device: str | None = None,
) -> EmbeddingService:
    """Return a cached embedding service instance."""
    return EmbeddingService(model_name=model_name, device=device)
