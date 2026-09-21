"""Document parsing and service tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from local_ai.core.exceptions import DocumentError
from local_ai.core.models import DocumentStatus
from local_ai.services.document_parser import extract_text
from local_ai.services.document_service import DocumentService
from local_ai.services.embedding_service import EmbeddingService
from local_ai.utils.files import sanitize_filename


def test_sanitize_filename() -> None:
    assert sanitize_filename("../../etc/passwd.txt") == "passwd.txt"
    assert sanitize_filename("My Report (final).pdf") == "My_Report_final_.pdf"


def test_extract_text_txt(tmp_path: Path) -> None:
    path = tmp_path / "note.txt"
    path.write_text("Hello Local AI", encoding="utf-8")
    assert extract_text(path) == "Hello Local AI"


def test_extract_text_markdown(tmp_path: Path) -> None:
    path = tmp_path / "note.md"
    path.write_text("# Title\n\nBody", encoding="utf-8")
    assert "Title" in extract_text(path)


def test_extract_unsupported(tmp_path: Path) -> None:
    path = tmp_path / "image.png"
    path.write_bytes(b"not-an-image")
    with pytest.raises(DocumentError):
        extract_text(path)


def test_document_import_and_index(
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

    service = DocumentService(tmp_db, embedding, chunk_size=80, chunk_overlap=10)
    source = tmp_path / "guide.txt"
    source.write_text(
        "Local AI keeps data private. " * 20,
        encoding="utf-8",
    )
    document = service.import_document(source, title="Guide")
    assert document.status == DocumentStatus.PENDING
    assert Path(document.stored_path).exists()

    indexed = service.index_document(document.id)
    assert indexed.status == DocumentStatus.READY
    assert indexed.chunk_count > 0
    assert service.get_chunks(document.id)

    service.delete_document(document.id)
    assert service.get_document(document.id) is None
