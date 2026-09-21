# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2026-09-21

### Fixed

- Multi-turn chat no longer gets stuck after the first reply
- Chat composer accepts Enter to send (Shift+Enter for newline)

### Changed

- Default chat model recommendation: `qwen3:8b` (better fit for 8GB GPUs than oversized flagships)
- Polished UI theme, chat bubbles, focus states, and composer layout

## [1.0.0] - 2026-09-21

### Added

- Initial public release of Local AI
- Desktop UI with Home, Chat, Documents, Memory, Models, and Settings
- Ollama-backed streaming chat with cancellation
- Document import for PDF, DOCX, TXT, and Markdown
- Local embedding index and RAG citations
- Optional persistent local memory
- SQLite storage with versioned migrations
- Light / dark / system themes
- Windows PyInstaller packaging scripts
- Linux and macOS PyInstaller packaging scripts
- pytest suite, Ruff, mypy, and GitHub Actions CI
- Windows standalone release artifact (`LocalAI-windows-x64`)

[1.0.1]: https://github.com/LucaVerduyn/local-ai/releases/tag/v1.0.1
[1.0.0]: https://github.com/LucaVerduyn/local-ai/releases/tag/v1.0.0
