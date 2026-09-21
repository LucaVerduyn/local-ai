"""Optional persistent local AI memory."""

from __future__ import annotations

import logging

from local_ai.core.database import Database
from local_ai.core.models import MemoryItem
from local_ai.services.embedding_service import EmbeddingService
from local_ai.utils.timeutil import parse_sqlite_datetime, utc_now_iso
from local_ai.utils.vectors import cosine_similarity, deserialize_vector, serialize_vector

logger = logging.getLogger(__name__)


class MemoryService:
    """Store and retrieve short persistent memories for the assistant."""

    def __init__(self, db: Database, embedding_service: EmbeddingService) -> None:
        self.db = db
        self.embedding_service = embedding_service

    def list_items(self, *, query: str | None = None) -> list[MemoryItem]:
        sql = "SELECT * FROM memory_items"
        params: list[object] = []
        if query:
            sql += " WHERE content LIKE ? OR tags LIKE ?"
            like = f"%{query}%"
            params.extend([like, like])
        sql += " ORDER BY importance DESC, updated_at DESC"
        return [self._row_to_item(row) for row in self.db.fetchall(sql, params)]

    def get(self, memory_id: int) -> MemoryItem | None:
        row = self.db.fetchone("SELECT * FROM memory_items WHERE id = ?", (memory_id,))
        return self._row_to_item(row) if row else None

    def add(self, content: str, *, tags: str = "", importance: int = 1) -> MemoryItem:
        cleaned = content.strip()
        if not cleaned:
            raise ValueError("Memory content cannot be empty")
        now = utc_now_iso()
        with self.db.cursor() as cur:
            cur.execute(
                """
                INSERT INTO memory_items (content, tags, importance, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (cleaned, tags.strip(), max(1, min(importance, 5)), now, now),
            )
            memory_id = int(cur.lastrowid or 0)

        self._index_memory(memory_id, cleaned)
        item = self.get(memory_id)
        assert item is not None
        return item

    def update(
        self,
        memory_id: int,
        *,
        content: str | None = None,
        tags: str | None = None,
        importance: int | None = None,
    ) -> MemoryItem:
        item = self.get(memory_id)
        if item is None:
            raise ValueError(f"Memory {memory_id} not found")

        new_content = content.strip() if content is not None else item.content
        new_tags = tags.strip() if tags is not None else item.tags
        new_importance = max(1, min(importance, 5)) if importance is not None else item.importance
        self.db.execute(
            """
            UPDATE memory_items
            SET content = ?, tags = ?, importance = ?, updated_at = ?
            WHERE id = ?
            """,
            (new_content, new_tags, new_importance, utc_now_iso(), memory_id),
        )
        if content is not None:
            self._index_memory(memory_id, new_content)
        updated = self.get(memory_id)
        assert updated is not None
        return updated

    def delete(self, memory_id: int) -> None:
        self.db.execute("DELETE FROM memory_items WHERE id = ?", (memory_id,))

    def search(self, query: str, *, top_k: int = 5, min_score: float = 0.2) -> list[MemoryItem]:
        cleaned = query.strip()
        if not cleaned:
            return []
        query_vector = self.embedding_service.embed(cleaned)
        rows = self.db.fetchall(
            """
            SELECT m.*, e.vector AS vector
            FROM memory_items m
            JOIN memory_embeddings e ON e.memory_id = m.id
            """
        )
        scored: list[tuple[float, MemoryItem]] = []
        for row in rows:
            vector = deserialize_vector(bytes(row["vector"]))
            score = cosine_similarity(query_vector, vector)
            if score >= min_score:
                scored.append((score, self._row_to_item(row)))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [item for _, item in scored[:top_k]]

    def build_memory_block(self, items: list[MemoryItem]) -> str:
        if not items:
            return ""
        lines = ["Known facts about the user / preferences:"]
        for item in items:
            tag_part = f" ({item.tags})" if item.tags else ""
            lines.append(f"- {item.content}{tag_part}")
        return "\n".join(lines)

    def _index_memory(self, memory_id: int, content: str) -> None:
        vector = self.embedding_service.embed(content)
        self.db.execute("DELETE FROM memory_embeddings WHERE memory_id = ?", (memory_id,))
        self.db.execute(
            """
            INSERT INTO memory_embeddings (memory_id, model, dimensions, vector)
            VALUES (?, ?, ?, ?)
            """,
            (
                memory_id,
                self.embedding_service.model,
                int(vector.shape[0]),
                serialize_vector(vector),
            ),
        )

    @staticmethod
    def _row_to_item(row: object) -> MemoryItem:
        data = row
        return MemoryItem(
            id=int(data["id"]),  # type: ignore[index]
            content=str(data["content"]),  # type: ignore[index]
            tags=str(data["tags"]),  # type: ignore[index]
            created_at=parse_sqlite_datetime(str(data["created_at"])),  # type: ignore[index]
            updated_at=parse_sqlite_datetime(str(data["updated_at"])),  # type: ignore[index]
            importance=int(data["importance"]),  # type: ignore[index]
        )
