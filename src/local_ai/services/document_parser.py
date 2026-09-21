"""Document text extraction for supported formats."""

from __future__ import annotations

from pathlib import Path

from local_ai.core.exceptions import DocumentError


def extract_text(path: Path) -> str:
    """Extract plain text from a supported document file."""
    suffix = path.suffix.lower()
    try:
        if suffix == ".pdf":
            return _extract_pdf(path)
        if suffix == ".docx":
            return _extract_docx(path)
        if suffix in {".txt", ".md", ".markdown"}:
            return path.read_text(encoding="utf-8", errors="replace")
    except DocumentError:
        raise
    except Exception as exc:
        raise DocumentError(f"Failed to read '{path.name}': {exc}") from exc
    raise DocumentError(f"Unsupported file type: {suffix}")


def _extract_pdf(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    parts: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            parts.append(text.strip())
    if not parts:
        raise DocumentError(f"No extractable text found in PDF '{path.name}'")
    return "\n\n".join(parts)


def _extract_docx(path: Path) -> str:
    from docx import Document as DocxDocument

    document = DocxDocument(str(path))
    parts = [p.text.strip() for p in document.paragraphs if p.text and p.text.strip()]
    if not parts:
        raise DocumentError(f"No extractable text found in DOCX '{path.name}'")
    return "\n\n".join(parts)
