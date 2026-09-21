"""Chat, RAG, and memory integration tests with fake Ollama."""

from __future__ import annotations

from pathlib import Path

import pytest

from local_ai.core.settings import SettingsStore
from local_ai.services.chat_service import ChatService
from local_ai.services.document_service import DocumentService
from local_ai.services.embedding_service import EmbeddingService
from local_ai.services.memory_service import MemoryService
from local_ai.services.rag_service import RAGService
from tests.fakes import FakeOllama


def test_chat_stream_persists_assistant_message(
    tmp_db,
    settings: SettingsStore,
    fake_ollama: FakeOllama,
    embedding: EmbeddingService,
) -> None:
    rag = RAGService(tmp_db, embedding)
    memory = MemoryService(tmp_db, embedding)
    chat = ChatService(tmp_db, settings, fake_ollama, rag, memory)

    conversation = chat.create_conversation(title="Test")
    chat.add_user_message(conversation.id, "Hello there")

    tokens: list[str] = []
    citations_final = None
    for item in chat.stream_assistant_reply(conversation.id):
        if isinstance(item, list):
            citations_final = item
        else:
            tokens.append(item)

    assert "".join(tokens) == "Hello from Local AI"
    assert citations_final == []
    messages = chat.get_messages(conversation.id)
    assert len(messages) == 2
    assert messages[-1].content == "Hello from Local AI"


def test_memory_add_and_search(tmp_db, embedding: EmbeddingService) -> None:
    memory = MemoryService(tmp_db, embedding)
    item = memory.add("User prefers Python examples", tags="prefs", importance=3)
    assert item.id > 0
    listed = memory.list_items()
    assert len(listed) == 1
    found = memory.search("Python examples", min_score=0.1)
    assert found
    memory.delete(item.id)
    assert memory.list_items() == []


def test_rag_search_returns_citations(
    tmp_db,
    embedding: EmbeddingService,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    storage = tmp_path / "docs"
    storage.mkdir()
    monkeypatch.setattr(
        "local_ai.utils.files.documents_storage_dir",
        lambda: storage,
    )

    docs = DocumentService(tmp_db, embedding, chunk_size=100, chunk_overlap=10)
    source = tmp_path / "policy.txt"
    source.write_text(
        "The privacy policy states that Local AI never uploads documents to the cloud. " * 10,
        encoding="utf-8",
    )
    document = docs.import_document(source, title="Policy")
    docs.index_document(document.id)

    rag = RAGService(tmp_db, embedding)
    citations = rag.search("privacy policy cloud upload", top_k=3, min_score=0.0)
    assert citations
    assert citations[0].document_title == "Policy"
    assert rag.build_context_block(citations)
