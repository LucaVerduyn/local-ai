"""Embedding generation via Ollama."""

from __future__ import annotations

import logging

import numpy as np
from numpy.typing import NDArray

from local_ai.core.exceptions import EmbeddingError, OllamaError
from local_ai.services.ollama_client import OllamaClient

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Create embeddings using a local Ollama embedding model."""

    def __init__(self, client: OllamaClient, model: str) -> None:
        self.client = client
        self.model = model

    def embed(self, text: str) -> NDArray[np.float32]:
        cleaned = text.strip()
        if not cleaned:
            raise EmbeddingError("Cannot embed empty text")
        try:
            values = self.client.embed(self.model, cleaned)
            return np.asarray(values, dtype=np.float32)
        except OllamaError as exc:
            raise EmbeddingError(str(exc)) from exc

    def embed_many(self, texts: list[str]) -> list[NDArray[np.float32]]:
        return [self.embed(text) for text in texts]
