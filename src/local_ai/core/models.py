"""Typed domain models used across Local AI."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class MessageRole(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class DocumentStatus(StrEnum):
    PENDING = "pending"
    INDEXING = "indexing"
    READY = "ready"
    ERROR = "error"


class ThemeMode(StrEnum):
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


@dataclass(slots=True)
class Conversation:
    id: int
    title: str
    model: str
    created_at: datetime
    updated_at: datetime
    use_documents: bool = True
    use_memory: bool = True


@dataclass(slots=True)
class Message:
    id: int
    conversation_id: int
    role: MessageRole
    content: str
    created_at: datetime
    sources: list[Citation] = field(default_factory=list)


@dataclass(slots=True)
class Citation:
    document_id: int
    document_title: str
    chunk_id: int
    excerpt: str
    score: float


@dataclass(slots=True)
class Document:
    id: int
    title: str
    filename: str
    source_path: str
    stored_path: str
    mime_type: str
    status: DocumentStatus
    error_message: str | None
    chunk_count: int
    created_at: datetime
    updated_at: datetime
    file_size: int = 0


@dataclass(slots=True)
class DocumentChunk:
    id: int
    document_id: int
    chunk_index: int
    content: str
    token_estimate: int


@dataclass(slots=True)
class MemoryItem:
    id: int
    content: str
    tags: str
    created_at: datetime
    updated_at: datetime
    importance: int = 1


@dataclass(slots=True)
class OllamaModelInfo:
    name: str
    size: int
    modified_at: str
    digest: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AppSettings:
    ollama_base_url: str
    chat_model: str
    embedding_model: str
    temperature: float
    context_chunks: int
    chunk_size: int
    chunk_overlap: int
    memory_enabled: bool
    theme: ThemeMode
    system_prompt: str
