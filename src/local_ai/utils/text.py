"""Text chunking utilities for RAG."""

from __future__ import annotations


def chunk_text(text: str, *, chunk_size: int = 800, overlap: int = 120) -> list[str]:
    """Split text into overlapping character-based chunks on paragraph/sentence boundaries."""
    cleaned = "\n".join(line.rstrip() for line in text.replace("\r\n", "\n").split("\n"))
    cleaned = cleaned.strip()
    if not cleaned:
        return []

    if len(cleaned) <= chunk_size:
        return [cleaned]

    chunks: list[str] = []
    start = 0
    length = len(cleaned)

    while start < length:
        end = min(start + chunk_size, length)
        if end < length:
            window = cleaned[start:end]
            break_at = max(
                window.rfind("\n\n"), window.rfind("\n"), window.rfind(". "), window.rfind(" ")
            )
            if break_at > chunk_size // 3:
                end = start + break_at + 1

        piece = cleaned[start:end].strip()
        if piece:
            chunks.append(piece)

        if end >= length:
            break
        start = max(end - overlap, start + 1)

    return chunks
