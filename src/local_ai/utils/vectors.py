"""Vector encoding helpers for SQLite-backed embeddings."""

from __future__ import annotations

import struct

import numpy as np
from numpy.typing import NDArray


def serialize_vector(vector: NDArray[np.float32]) -> bytes:
    """Serialize a float32 vector to bytes."""
    flat = np.asarray(vector, dtype=np.float32).ravel()
    return struct.pack(f"<{len(flat)}f", *flat.tolist())


def deserialize_vector(data: bytes) -> NDArray[np.float32]:
    """Deserialize bytes into a float32 numpy vector."""
    count = len(data) // 4
    values = struct.unpack(f"<{count}f", data)
    return np.asarray(values, dtype=np.float32)


def cosine_similarity(a: NDArray[np.float32], b: NDArray[np.float32]) -> float:
    """Compute cosine similarity between two vectors."""
    a_norm = float(np.linalg.norm(a))
    b_norm = float(np.linalg.norm(b))
    if a_norm == 0.0 or b_norm == 0.0:
        return 0.0
    return float(np.dot(a, b) / (a_norm * b_norm))


def estimate_tokens(text: str) -> int:
    """Rough token estimate (~4 chars per token)."""
    return max(1, len(text) // 4)
