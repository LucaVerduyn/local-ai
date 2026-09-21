"""SQLite database access and schema migrations."""

from __future__ import annotations

import logging
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import cast

from local_ai.core.exceptions import DatabaseError
from local_ai.core.migrations import CURRENT_SCHEMA_VERSION, MIGRATIONS

logger = logging.getLogger(__name__)


class Database:
    """Thin SQLite wrapper with schema versioning."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._connection: sqlite3.Connection | None = None

    def connect(self) -> sqlite3.Connection:
        if self._connection is None:
            try:
                conn = sqlite3.connect(
                    self.path,
                    check_same_thread=False,
                    detect_types=sqlite3.PARSE_DECLTYPES,
                )
                conn.row_factory = sqlite3.Row
                conn.execute("PRAGMA foreign_keys = ON")
                conn.execute("PRAGMA journal_mode = WAL")
                self._connection = conn
            except sqlite3.Error as exc:
                raise DatabaseError(f"Failed to open database: {exc}") from exc
        return self._connection

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    @contextmanager
    def cursor(self) -> Iterator[sqlite3.Cursor]:
        conn = self.connect()
        cur = conn.cursor()
        try:
            yield cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()

    def execute(self, sql: str, params: tuple[object, ...] | list[object] = ()) -> sqlite3.Cursor:
        with self.cursor() as cur:
            return cur.execute(sql, params)

    def executemany(
        self, sql: str, seq: list[tuple[object, ...]] | list[list[object]]
    ) -> sqlite3.Cursor:
        with self.cursor() as cur:
            return cur.executemany(sql, seq)

    def fetchone(
        self, sql: str, params: tuple[object, ...] | list[object] = ()
    ) -> sqlite3.Row | None:
        conn = self.connect()
        cur = conn.execute(sql, params)
        return cast(sqlite3.Row | None, cur.fetchone())

    def fetchall(
        self, sql: str, params: tuple[object, ...] | list[object] = ()
    ) -> list[sqlite3.Row]:
        conn = self.connect()
        cur = conn.execute(sql, params)
        return list(cur.fetchall())

    def migrate(self) -> None:
        """Apply pending schema migrations."""
        conn = self.connect()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        conn.commit()

        row = conn.execute(
            "SELECT COALESCE(MAX(version), 0) AS v FROM schema_migrations"
        ).fetchone()
        current = int(row["v"]) if row else 0
        logger.info("Database schema version: %s (target %s)", current, CURRENT_SCHEMA_VERSION)

        for version, sql in MIGRATIONS:
            if version <= current:
                continue
            logger.info("Applying migration v%s", version)
            try:
                conn.executescript(sql)
                conn.execute("INSERT INTO schema_migrations (version) VALUES (?)", (version,))
                conn.commit()
            except sqlite3.Error as exc:
                conn.rollback()
                raise DatabaseError(f"Migration v{version} failed: {exc}") from exc
