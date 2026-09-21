"""Datetime parsing helpers."""

from __future__ import annotations

from datetime import UTC, datetime


def parse_sqlite_datetime(value: str) -> datetime:
    """Parse SQLite datetime strings into timezone-aware UTC datetimes."""
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=UTC)
        except ValueError:
            continue
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def utc_now_iso() -> str:
    """Return current UTC time as SQLite-friendly ISO string."""
    return datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
