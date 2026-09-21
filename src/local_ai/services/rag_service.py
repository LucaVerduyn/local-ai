"""Retrieval-augmented generation helpers."""

from __future__ import annotations

import logging

from local_ai.core.database import Database
from local_ai.core.models import Citation, DocumentStatus
from local_ai.services.embedding_service import EmbeddingService
from local_ai.utils.vectors import cosine_similarity, deserialize_vector

logger = logging.getLogger(__name__)


class RAGService:
    """Semantic search over indexed document chunks."""

    def __init__(self, db: Database, embedding_service: EmbeddingService) -> None:
        self.db = db
        self.embedding_service = embedding_service

    def search(self, query: str, *, top_k: int = 5, min_score: float = 0.15) -> list[Citation]:
        cleaned = query.strip()
        if not cleaned:
            return []

        query_vector = self.embedding_service.embed(cleaned)
        rows = self.db.fetchall(
            """
            SELECT
                c.id AS chunk_id,
                c.document_id AS document_id,
                c.content AS content,
                d.title AS document_title,
                e.vector AS vector,
                e.model AS model
            FROM embeddings e
            JOIN document_chunks c ON c.id = e.chunk_id
            JOIN documents d ON d.id = c.document_id
            WHERE d.status = ?
            """,
            (DocumentStatus.READY.value,),
        )
        if not rows:
            return []

        scored: list[Citation] = []
        for row in rows:
            vector = deserialize_vector(bytes(row["vector"]))
            score = cosine_similarity(query_vector, vector)
            if score < min_score:
                continue
            excerpt = str(row["content"])
            if len(excerpt) > 400:
                excerpt = excerpt[:397] + "…"
            scored.append(
                Citation(
                    document_id=int(row["document_id"]),
                    document_title=str(row["document_title"]),
                    chunk_id=int(row["chunk_id"]),
                    excerpt=excerpt,
                    score=score,
                )
            )

        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:top_k]

    def build_context_block(self, citations: list[Citation]) -> str:
        if not citations:
            return ""
        parts = ["Relevant document excerpts:"]
        for index, citation in enumerate(citations, start=1):
            parts.append(
                f"[{index}] {citation.document_title} (score {citation.score:.2f})\n"
                f"{citation.excerpt}"
            )
        return "\n\n".join(parts)
