# Local AI

Privacy-first desktop AI workspace powered by local language models.

Local AI is a **real desktop application** (Python + PySide6/Qt) for chatting with local LLMs, importing documents, asking questions with local RAG, and keeping optional AI memory — all without accounts, subscriptions, paid API keys, or a cloud backend.

## Features

- **Local chat** with streaming responses and cancellation
- **Ollama** as the default AI backend
- **Document import** for PDF, DOCX, TXT, and Markdown
- **Local RAG** with embeddings, semantic search, and source citations
- **Optional persistent memory** stored only on your device
- **Conversation history** with search
- **Models management** (list / pull / delete / assign chat & embedding models)
- **Light, dark, and system themes**
- **SQLite** storage with schema migrations
- **Standalone Windows packaging** via PyInstaller

## Privacy model

- Chats, documents, embeddings, and memories stay on your machine
- Inference is sent only to the Ollama instance you configure (default: `http://127.0.0.1:11434`)
- No telemetry, analytics, accounts, or forced cloud sync
- Imported files are copied into Local AI’s local data directory

## Requirements

- Windows, macOS, or Linux
- [Ollama](https://ollama.com) installed and running
- Python **3.13+** (for development); end users can use the packaged Windows build

### Recommended Ollama models

```bash
ollama pull llama3.2
ollama pull nomic-embed-text
```

Any chat-capable Ollama model works. For RAG/memory, use an embedding model such as `nomic-embed-text`.

## Installation (from source)

```bash
git clone https://github.com/LucaVerduyn/local-ai.git
cd local-ai
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -e ".[dev]"
local-ai
```

Or:

```bash
python -m local_ai
```

## Ollama setup

1. Install Ollama from https://ollama.com
2. Start the Ollama service
3. Pull a chat model and an embedding model (see above)
4. Open **Models** in Local AI and confirm the connection
5. Optionally set default chat/embedding models in **Settings**

If Ollama runs on another host/port, change **Ollama URL** in Settings.

## Usage

1. Open **Home** to verify Ollama status
2. Start a chat in **Chat**
3. Import files in **Documents** (they are indexed in the background)
4. Enable **Use documents** on a conversation for RAG answers with citations
5. Add optional notes in **Memory**
6. Tune models and theme in **Settings**

Data locations (platform-specific via `platformdirs`):

- Database & document copies — user data directory for `local-ai`
- Settings — user config directory
- Logs — user log directory

## Development

```bash
pip install -e ".[dev]"
ruff check src tests
ruff format src tests
mypy src
pytest
```

Architecture overview:

- `src/local_ai/core` — database, migrations, settings, models
- `src/local_ai/services` — Ollama, chat, documents, RAG, memory, embeddings
- `src/local_ai/workers` — background Qt threads (non-blocking UI)
- `src/local_ai/ui` — main window, themes, views, widgets

See [docs/architecture.md](docs/architecture.md) and [docs/development.md](docs/development.md).

## Testing

```bash
pytest
pytest --cov=local_ai
```

Tests use a fake Ollama client so core flows run without a live server. UI smoke tests use `pytest-qt`.

## Packaging (Windows)

```bash
pip install -e ".[packaging]"
powershell -File packaging/windows/build.ps1
```

The build writes a standalone folder under `packaging/windows/dist/LocalAI/`.

Linux/macOS packaging can follow the same layout later under `packaging/linux` and `packaging/macos`.

## Roadmap

- Conversation export / import
- Multi-document scoped chats
- Optional tool calling for local workflows
- Linux AppImage and macOS `.app` bundles
- Richer PDF table/layout extraction

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Please follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## Security

See [SECURITY.md](SECURITY.md).

## License

MIT © Luca Verduyn — see [LICENSE](LICENSE).
