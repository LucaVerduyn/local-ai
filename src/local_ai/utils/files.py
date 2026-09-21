"""Secure local file handling helpers."""

from __future__ import annotations

import hashlib
import re
import shutil
from pathlib import Path

from local_ai.config import SUPPORTED_DOCUMENT_EXTENSIONS, documents_storage_dir
from local_ai.core.exceptions import DocumentError

_SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")


def sanitize_filename(name: str) -> str:
    """Return a filesystem-safe filename."""
    base = Path(name).name
    cleaned = _SAFE_NAME.sub("_", base).strip("._")
    return cleaned or "document"


def ensure_supported_document(path: Path) -> Path:
    """Validate that a path exists and has a supported extension."""
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise DocumentError(f"File not found: {path}")
    if resolved.suffix.lower() not in SUPPORTED_DOCUMENT_EXTENSIONS:
        raise DocumentError(
            f"Unsupported file type '{resolved.suffix}'. "
            f"Supported: {', '.join(sorted(SUPPORTED_DOCUMENT_EXTENSIONS))}"
        )
    return resolved


def import_document_copy(source: Path, *, document_id: int | None = None) -> Path:
    """Copy a document into the local storage directory with a unique name."""
    source = ensure_supported_document(source)
    digest = hashlib.sha256(
        f"{source}:{document_id}:{source.stat().st_mtime}".encode()
    ).hexdigest()[:12]
    safe = sanitize_filename(source.name)
    destination = documents_storage_dir() / f"{digest}_{safe}"
    shutil.copy2(source, destination)
    return destination


def mime_for_path(path: Path) -> str:
    """Return a simple MIME type for a supported document."""
    mapping = {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".txt": "text/plain",
        ".md": "text/markdown",
        ".markdown": "text/markdown",
    }
    return mapping.get(path.suffix.lower(), "application/octet-stream")
