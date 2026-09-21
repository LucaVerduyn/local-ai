"""Document import, indexing, and management."""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path

from local_ai.core.database import Database
from local_ai.core.exceptions import DocumentError
from local_ai.core.models import Document, DocumentChunk, DocumentStatus
from local_ai.services.document_parser import extract_text
from local_ai.services.embedding_service import EmbeddingService
from local_ai.utils.files import ensure_supported_document, import_document_copy, mime_for_path
from local_ai.utils.text import chunk_text
from local_ai.utils.timeutil import parse_sqlite_datetime, utc_now_iso
from local_ai.utils.vectors import estimate_tokens, serialize_vector

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[str], None]


class DocumentService:
    """Manage local documents and their RAG indexes."""

    def __init__(
        self,
        db: Database,
        embedding_service: EmbeddingService,
        *,
        chunk_size: int = 800,
        chunk_overlap: int = 120,
    ) -> None:
        self.db = db
        self.embedding_service = embedding_service
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def list_documents(self, *, query: str | None = None) -> list[Document]:
        sql = "SELECT * FROM documents"
        params: list[object] = []
        if query:
            sql += " WHERE title LIKE ? OR filename LIKE ?"
            like = f"%{query}%"
            params.extend([like, like])
        sql += " ORDER BY updated_at DESC"
        return [self._row_to_document(row) for row in self.db.fetchall(sql, params)]

    def get_document(self, document_id: int) -> Document | None:
        row = self.db.fetchone("SELECT * FROM documents WHERE id = ?", (document_id,))
        return self._row_to_document(row) if row else None

    def import_document(self, path: Path, *, title: str | None = None) -> Document:
        source = ensure_supported_document(path)
        now = utc_now_iso()
        display_title = title or source.stem
        with self.db.cursor() as cur:
            cur.execute(
                """
                INSERT INTO documents (
                    title, filename, source_path, stored_path, mime_type,
                    status, error_message, chunk_count, file_size, created_at, updated_at
                ) VALUES (?, ?, ?, '', ?, ?, NULL, 0, ?, ?, ?)
                """,
                (
                    display_title,
                    source.name,
                    str(source),
                    mime_for_path(source),
                    DocumentStatus.PENDING.value,
                    source.stat().st_size,
                    now,
                    now,
                ),
            )
            document_id = int(cur.lastrowid or 0)

        stored = import_document_copy(source, document_id=document_id)
        self.db.execute(
            "UPDATE documents SET stored_path = ?, updated_at = ? WHERE id = ?",
            (str(stored), utc_now_iso(), document_id),
        )
        document = self.get_document(document_id)
        assert document is not None
        return document

    def index_document(
        self,
        document_id: int,
        *,
        progress: ProgressCallback | None = None,
        cancel_check: Callable[[], bool] | None = None,
    ) -> Document:
        document = self.get_document(document_id)
        if document is None:
            raise DocumentError(f"Document {document_id} not found")

        self._set_status(document_id, DocumentStatus.INDEXING)
        if progress:
            progress("Extracting text…")

        try:
            text = extract_text(Path(document.stored_path))
            if cancel_check and cancel_check():
                raise DocumentError("Indexing cancelled")

            if progress:
                progress("Chunking document…")
            chunks = chunk_text(
                text,
                chunk_size=self.chunk_size,
                overlap=self.chunk_overlap,
            )
            if not chunks:
                raise DocumentError("Document produced no text chunks")

            self._clear_chunks(document_id)
            chunk_ids: list[int] = []
            with self.db.cursor() as cur:
                for index, content in enumerate(chunks):
                    cur.execute(
                        """
                        INSERT INTO document_chunks (document_id, chunk_index, content, token_estimate)
                        VALUES (?, ?, ?, ?)
                        """,
                        (document_id, index, content, estimate_tokens(content)),
                    )
                    chunk_ids.append(int(cur.lastrowid or 0))

            model = self.embedding_service.model
            for i, (chunk_id, content) in enumerate(zip(chunk_ids, chunks, strict=True)):
                if cancel_check and cancel_check():
                    raise DocumentError("Indexing cancelled")
                if progress:
                    progress(f"Embedding chunk {i + 1}/{len(chunks)}…")
                vector = self.embedding_service.embed(content)
                self.db.execute(
                    """
                    INSERT INTO embeddings (chunk_id, model, dimensions, vector)
                    VALUES (?, ?, ?, ?)
                    """,
                    (chunk_id, model, int(vector.shape[0]), serialize_vector(vector)),
                )

            self.db.execute(
                """
                UPDATE documents
                SET status = ?, error_message = NULL, chunk_count = ?, updated_at = ?
                WHERE id = ?
                """,
                (DocumentStatus.READY.value, len(chunks), utc_now_iso(), document_id),
            )
            if progress:
                progress("Indexing complete")
        except Exception as exc:
            message = str(exc)
            logger.exception("Failed to index document %s", document_id)
            self._set_status(document_id, DocumentStatus.ERROR, error=message)
            raise DocumentError(message) from exc

        result = self.get_document(document_id)
        assert result is not None
        return result

    def delete_document(self, document_id: int) -> None:
        document = self.get_document(document_id)
        if document is None:
            return
        stored = Path(document.stored_path)
        self.db.execute("DELETE FROM documents WHERE id = ?", (document_id,))
        if stored.exists():
            try:
                stored.unlink()
            except OSError as exc:
                logger.warning("Could not delete stored file %s: %s", stored, exc)

    def get_chunks(self, document_id: int) -> list[DocumentChunk]:
        rows = self.db.fetchall(
            "SELECT * FROM document_chunks WHERE document_id = ? ORDER BY chunk_index",
            (document_id,),
        )
        return [
            DocumentChunk(
                id=int(row["id"]),
                document_id=int(row["document_id"]),
                chunk_index=int(row["chunk_index"]),
                content=str(row["content"]),
                token_estimate=int(row["token_estimate"]),
            )
            for row in rows
        ]

    def _clear_chunks(self, document_id: int) -> None:
        self.db.execute("DELETE FROM document_chunks WHERE document_id = ?", (document_id,))

    def _set_status(
        self,
        document_id: int,
        status: DocumentStatus,
        *,
        error: str | None = None,
    ) -> None:
        self.db.execute(
            """
            UPDATE documents
            SET status = ?, error_message = ?, updated_at = ?
            WHERE id = ?
            """,
            (status.value, error, utc_now_iso(), document_id),
        )

    @staticmethod
    def _row_to_document(row: object) -> Document:
        data = row  # sqlite3.Row
        return Document(
            id=int(data["id"]),  # type: ignore[index]
            title=str(data["title"]),  # type: ignore[index]
            filename=str(data["filename"]),  # type: ignore[index]
            source_path=str(data["source_path"]),  # type: ignore[index]
            stored_path=str(data["stored_path"]),  # type: ignore[index]
            mime_type=str(data["mime_type"]),  # type: ignore[index]
            status=DocumentStatus(str(data["status"])),  # type: ignore[index]
            error_message=data["error_message"],  # type: ignore[index]
            chunk_count=int(data["chunk_count"]),  # type: ignore[index]
            created_at=parse_sqlite_datetime(str(data["created_at"])),  # type: ignore[index]
            updated_at=parse_sqlite_datetime(str(data["updated_at"])),  # type: ignore[index]
            file_size=int(data["file_size"]),  # type: ignore[index]
        )
