"""Test doubles used across the suite."""

from __future__ import annotations

from collections.abc import Iterator

import numpy as np

from local_ai.core.models import OllamaModelInfo
from local_ai.services.ollama_client import CancelCallback, OllamaClient


class FakeOllama(OllamaClient):
    """Deterministic offline stand-in for Ollama."""

    def __init__(self) -> None:
        super().__init__("http://127.0.0.1:9")
        self.available = True
        self.chat_tokens = ["Hello", " from ", "Local AI"]

    def is_available(self) -> bool:
        return self.available

    def list_models(self) -> list[OllamaModelInfo]:
        return [
            OllamaModelInfo(name="llama3.2", size=1, modified_at="", digest="a"),
            OllamaModelInfo(name="nomic-embed-text", size=1, modified_at="", digest="b"),
        ]

    def embed(self, model: str, text: str) -> list[float]:
        """Bag-of-words style embedding so similar texts score highly."""
        _ = model
        vector = np.zeros(64, dtype=np.float32)
        tokens = text.lower().split()
        if not tokens:
            vector[0] = 1.0
            return vector.tolist()
        for token in tokens:
            index = abs(hash(token)) % 64
            vector[index] += 1.0
        norm = float(np.linalg.norm(vector))
        if norm > 0:
            vector /= norm
        return vector.tolist()

    def chat_stream(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        cancel_check: CancelCallback | None = None,
    ) -> Iterator[str]:
        _ = model, messages, temperature
        for token in self.chat_tokens:
            if cancel_check and cancel_check():
                break
            yield token
