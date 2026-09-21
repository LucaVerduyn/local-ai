"""Tests for text utilities and vector helpers."""

from __future__ import annotations

import numpy as np
import pytest

from local_ai.utils.text import chunk_text
from local_ai.utils.vectors import cosine_similarity, deserialize_vector, serialize_vector


def test_chunk_text_respects_size() -> None:
    text = "Paragraph one.\n\n" + ("word " * 200)
    chunks = chunk_text(text, chunk_size=120, overlap=20)
    assert len(chunks) > 1
    assert all(len(chunk) <= 160 for chunk in chunks)


def test_chunk_text_empty() -> None:
    assert chunk_text("   ") == []


def test_vector_roundtrip() -> None:
    original = np.asarray([0.1, -0.2, 0.3], dtype=np.float32)
    restored = deserialize_vector(serialize_vector(original))
    assert np.allclose(original, restored)


def test_cosine_similarity_identical() -> None:
    vector = np.asarray([1.0, 2.0, 3.0], dtype=np.float32)
    assert cosine_similarity(vector, vector) == pytest.approx(1.0)
