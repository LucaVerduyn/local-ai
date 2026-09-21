"""Conversation and chat orchestration."""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterator

from local_ai.core.database import Database
from local_ai.core.models import Citation, Conversation, Message, MessageRole
from local_ai.core.settings import SettingsStore
from local_ai.services.memory_service import MemoryService
from local_ai.services.ollama_client import OllamaClient
from local_ai.services.rag_service import RAGService
from local_ai.utils.timeutil import parse_sqlite_datetime, utc_now_iso

logger = logging.getLogger(__name__)

CancelCallback = Callable[[], bool]


class ChatService:
    """Create conversations and stream assistant replies with optional RAG/memory."""

    def __init__(
        self,
        db: Database,
        settings: SettingsStore,
        ollama: OllamaClient,
        rag: RAGService,
        memory: MemoryService,
    ) -> None:
        self.db = db
        self.settings = settings
        self.ollama = ollama
        self.rag = rag
        self.memory = memory

    def list_conversations(self, *, query: str | None = None) -> list[Conversation]:
        sql = "SELECT * FROM conversations"
        params: list[object] = []
        if query:
            sql += " WHERE title LIKE ?"
            params.append(f"%{query}%")
        sql += " ORDER BY updated_at DESC"
        return [self._row_to_conversation(row) for row in self.db.fetchall(sql, params)]

    def get_conversation(self, conversation_id: int) -> Conversation | None:
        row = self.db.fetchone("SELECT * FROM conversations WHERE id = ?", (conversation_id,))
        return self._row_to_conversation(row) if row else None

    def create_conversation(
        self,
        *,
        title: str = "New chat",
        model: str | None = None,
        use_documents: bool = True,
        use_memory: bool = True,
    ) -> Conversation:
        cfg = self.settings.settings
        now = utc_now_iso()
        with self.db.cursor() as cur:
            cur.execute(
                """
                INSERT INTO conversations (title, model, use_documents, use_memory, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    title,
                    model or cfg.chat_model,
                    int(use_documents),
                    int(use_memory),
                    now,
                    now,
                ),
            )
            conversation_id = int(cur.lastrowid or 0)
        result = self.get_conversation(conversation_id)
        assert result is not None
        return result

    def rename_conversation(self, conversation_id: int, title: str) -> None:
        self.db.execute(
            "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
            (title.strip() or "Untitled", utc_now_iso(), conversation_id),
        )

    def delete_conversation(self, conversation_id: int) -> None:
        self.db.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))

    def set_flags(
        self,
        conversation_id: int,
        *,
        use_documents: bool | None = None,
        use_memory: bool | None = None,
        model: str | None = None,
    ) -> None:
        conversation = self.get_conversation(conversation_id)
        if conversation is None:
            return
        self.db.execute(
            """
            UPDATE conversations
            SET use_documents = ?, use_memory = ?, model = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                int(conversation.use_documents if use_documents is None else use_documents),
                int(conversation.use_memory if use_memory is None else use_memory),
                model or conversation.model,
                utc_now_iso(),
                conversation_id,
            ),
        )

    def get_messages(self, conversation_id: int) -> list[Message]:
        rows = self.db.fetchall(
            """
            SELECT * FROM messages
            WHERE conversation_id = ?
            ORDER BY created_at ASC, id ASC
            """,
            (conversation_id,),
        )
        messages: list[Message] = []
        for row in rows:
            message = self._row_to_message(row)
            message.sources = self._get_citations(message.id)
            messages.append(message)
        return messages

    def add_user_message(self, conversation_id: int, content: str) -> Message:
        cleaned = content.strip()
        if not cleaned:
            raise ValueError("Message cannot be empty")
        now = utc_now_iso()
        with self.db.cursor() as cur:
            cur.execute(
                """
                INSERT INTO messages (conversation_id, role, content, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (conversation_id, MessageRole.USER.value, cleaned, now),
            )
            message_id = int(cur.lastrowid or 0)
        self.db.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (now, conversation_id),
        )
        conversation = self.get_conversation(conversation_id)
        if conversation and conversation.title == "New chat":
            title = cleaned[:60] + ("…" if len(cleaned) > 60 else "")
            self.rename_conversation(conversation_id, title)
        messages = [m for m in self.get_messages(conversation_id) if m.id == message_id]
        return messages[0]

    def stream_assistant_reply(
        self,
        conversation_id: int,
        *,
        cancel_check: CancelCallback | None = None,
    ) -> Iterator[str | list[Citation]]:
        """
        Stream assistant tokens, then yield the final citations list once.

        Yields:
            str tokens while generating, then a list[Citation] as the final item.
        """
        conversation = self.get_conversation(conversation_id)
        if conversation is None:
            raise ValueError(f"Conversation {conversation_id} not found")

        cfg = self.settings.settings
        history = self.get_messages(conversation_id)
        if not history or history[-1].role != MessageRole.USER:
            raise ValueError("Conversation has no pending user message")

        user_query = history[-1].content
        citations: list[Citation] = []
        memory_block = ""
        context_block = ""

        if conversation.use_documents:
            try:
                citations = self.rag.search(user_query, top_k=cfg.context_chunks)
                context_block = self.rag.build_context_block(citations)
            except Exception:
                logger.exception("RAG retrieval failed; continuing without documents")

        if conversation.use_memory and cfg.memory_enabled:
            try:
                memories = self.memory.search(user_query, top_k=5)
                memory_block = self.memory.build_memory_block(memories)
            except Exception:
                logger.exception("Memory retrieval failed; continuing without memory")

        system_parts = [cfg.system_prompt]
        if memory_block:
            system_parts.append(memory_block)
        if context_block:
            system_parts.append(
                context_block
                + "\n\nUse the excerpts above when relevant. Mention document titles when citing."
            )

        api_messages: list[dict[str, str]] = [
            {"role": "system", "content": "\n\n".join(system_parts)}
        ]
        for message in history:
            if message.role == MessageRole.SYSTEM:
                continue
            api_messages.append({"role": message.role.value, "content": message.content})

        assembled: list[str] = []
        for token in self.ollama.chat_stream(
            model=conversation.model,
            messages=api_messages,
            temperature=cfg.temperature,
            cancel_check=cancel_check,
        ):
            assembled.append(token)
            yield token

        full = "".join(assembled).strip()
        if not full:
            full = "(Generation cancelled or produced no output.)"

        now = utc_now_iso()
        with self.db.cursor() as cur:
            cur.execute(
                """
                INSERT INTO messages (conversation_id, role, content, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (conversation_id, MessageRole.ASSISTANT.value, full, now),
            )
            message_id = int(cur.lastrowid or 0)
            for citation in citations:
                cur.execute(
                    """
                    INSERT INTO message_citations (
                        message_id, document_id, document_title, chunk_id, excerpt, score
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        message_id,
                        citation.document_id,
                        citation.document_title,
                        citation.chunk_id,
                        citation.excerpt,
                        citation.score,
                    ),
                )
        self.db.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (now, conversation_id),
        )
        yield citations

    def search_messages(self, query: str, *, limit: int = 50) -> list[tuple[Conversation, Message]]:
        like = f"%{query.strip()}%"
        if not query.strip():
            return []
        rows = self.db.fetchall(
            """
            SELECT m.*, c.title AS conversation_title, c.model AS conversation_model,
                   c.use_documents, c.use_memory, c.created_at AS c_created,
                   c.updated_at AS c_updated
            FROM messages m
            JOIN conversations c ON c.id = m.conversation_id
            WHERE m.content LIKE ?
            ORDER BY m.created_at DESC
            LIMIT ?
            """,
            (like, limit),
        )
        results: list[tuple[Conversation, Message]] = []
        for row in rows:
            conversation = Conversation(
                id=int(row["conversation_id"]),
                title=str(row["conversation_title"]),
                model=str(row["conversation_model"]),
                created_at=parse_sqlite_datetime(str(row["c_created"])),
                updated_at=parse_sqlite_datetime(str(row["c_updated"])),
                use_documents=bool(row["use_documents"]),
                use_memory=bool(row["use_memory"]),
            )
            results.append((conversation, self._row_to_message(row)))
        return results

    def _get_citations(self, message_id: int) -> list[Citation]:
        rows = self.db.fetchall(
            "SELECT * FROM message_citations WHERE message_id = ? ORDER BY score DESC",
            (message_id,),
        )
        return [
            Citation(
                document_id=int(row["document_id"]),
                document_title=str(row["document_title"]),
                chunk_id=int(row["chunk_id"]),
                excerpt=str(row["excerpt"]),
                score=float(row["score"]),
            )
            for row in rows
        ]

    @staticmethod
    def _row_to_conversation(row: object) -> Conversation:
        data = row
        return Conversation(
            id=int(data["id"]),  # type: ignore[index]
            title=str(data["title"]),  # type: ignore[index]
            model=str(data["model"]),  # type: ignore[index]
            created_at=parse_sqlite_datetime(str(data["created_at"])),  # type: ignore[index]
            updated_at=parse_sqlite_datetime(str(data["updated_at"])),  # type: ignore[index]
            use_documents=bool(data["use_documents"]),  # type: ignore[index]
            use_memory=bool(data["use_memory"]),  # type: ignore[index]
        )

    @staticmethod
    def _row_to_message(row: object) -> Message:
        data = row
        return Message(
            id=int(data["id"]),  # type: ignore[index]
            conversation_id=int(data["conversation_id"]),  # type: ignore[index]
            role=MessageRole(str(data["role"])),  # type: ignore[index]
            content=str(data["content"]),  # type: ignore[index]
            created_at=parse_sqlite_datetime(str(data["created_at"])),  # type: ignore[index]
        )
