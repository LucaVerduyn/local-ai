# Architecture

Local AI is a modular desktop application.

```
┌──────────────────────────────────────────────┐
│                   UI (PySide6)               │
│  Home · Chat · Documents · Memory · Models   │
└──────────────────────┬───────────────────────┘
                       │ signals / slots
┌──────────────────────▼───────────────────────┐
│              Workers (QThread)               │
│     chat streaming · indexing · pulls        │
└──────────────────────┬───────────────────────┘
                       │
┌──────────────────────▼───────────────────────┐
│                   Services                   │
│ Chat · Documents · RAG · Memory · Embeddings │
│              Ollama HTTP client              │
└──────────────────────┬───────────────────────┘
                       │
┌──────────────────────▼───────────────────────┐
│              Core / Persistence              │
│     SQLite (+ migrations) · Settings JSON    │
└──────────────────────────────────────────────┘
```

## Data flow

1. User sends a chat message
2. Chat service stores the user message in SQLite
3. Optional RAG retrieval embeds the query and ranks document chunks
4. Optional memory search adds personal context
5. Ollama streams tokens on a worker thread
6. UI appends tokens live; final message and citations are persisted

## Storage

- `conversations`, `messages`, `message_citations`
- `documents`, `document_chunks`, `embeddings`
- `memory_items`, `memory_embeddings`
- Schema version tracked in `schema_migrations`

Embeddings are float32 blobs. Similarity is cosine similarity in-process with NumPy.

## Privacy boundary

The only network dependency is the configured Ollama base URL. Everything else is local filesystem + SQLite.
