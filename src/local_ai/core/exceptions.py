"""Domain and infrastructure exceptions."""

from __future__ import annotations


class LocalAIError(Exception):
    """Base exception for Local AI."""


class OllamaError(LocalAIError):
    """Raised when the Ollama backend fails or is unreachable."""


class OllamaConnectionError(OllamaError):
    """Raised when Ollama cannot be reached."""


class DocumentError(LocalAIError):
    """Raised for document import or parsing failures."""


class DatabaseError(LocalAIError):
    """Raised for database failures."""


class EmbeddingError(LocalAIError):
    """Raised when embedding generation fails."""


class CancellationError(LocalAIError):
    """Raised when a long-running operation is cancelled."""
