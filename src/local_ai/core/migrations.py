"""Versioned SQL migrations for Local AI."""

from __future__ import annotations

CURRENT_SCHEMA_VERSION = 1

MIGRATIONS: list[tuple[int, str]] = [
    (
        1,
        """
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            model TEXT NOT NULL,
            use_documents INTEGER NOT NULL DEFAULT 1,
            use_memory INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS message_citations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER NOT NULL,
            document_id INTEGER NOT NULL,
            document_title TEXT NOT NULL,
            chunk_id INTEGER NOT NULL,
            excerpt TEXT NOT NULL,
            score REAL NOT NULL,
            FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            filename TEXT NOT NULL,
            source_path TEXT NOT NULL,
            stored_path TEXT NOT NULL,
            mime_type TEXT NOT NULL,
            status TEXT NOT NULL,
            error_message TEXT,
            chunk_count INTEGER NOT NULL DEFAULT 0,
            file_size INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS document_chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,
            token_estimate INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
            UNIQUE (document_id, chunk_index)
        );

        CREATE TABLE IF NOT EXISTS embeddings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chunk_id INTEGER NOT NULL UNIQUE,
            model TEXT NOT NULL,
            dimensions INTEGER NOT NULL,
            vector BLOB NOT NULL,
            FOREIGN KEY (chunk_id) REFERENCES document_chunks(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS memory_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            tags TEXT NOT NULL DEFAULT '',
            importance INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS memory_embeddings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            memory_id INTEGER NOT NULL UNIQUE,
            model TEXT NOT NULL,
            dimensions INTEGER NOT NULL,
            vector BLOB NOT NULL,
            FOREIGN KEY (memory_id) REFERENCES memory_items(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_messages_conversation
            ON messages(conversation_id, created_at);
        CREATE INDEX IF NOT EXISTS idx_chunks_document
            ON document_chunks(document_id);
        CREATE INDEX IF NOT EXISTS idx_documents_status
            ON documents(status);
        CREATE INDEX IF NOT EXISTS idx_conversations_updated
            ON conversations(updated_at DESC);
        """,
    ),
]
