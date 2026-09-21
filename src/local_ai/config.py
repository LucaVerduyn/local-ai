"""Paths, constants, and application-wide configuration helpers."""

from __future__ import annotations

from pathlib import Path

from platformdirs import user_config_dir, user_data_dir, user_log_dir

from local_ai import __app_name__, __author__

APP_ID = "local-ai"
ORG_NAME = __author__
APP_NAME = __app_name__

DEFAULT_OLLAMA_BASE_URL = "http://127.0.0.1:11434"
DEFAULT_CHAT_MODEL = "qwen3:8b"
DEFAULT_EMBEDDING_MODEL = "nomic-embed-text"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_CONTEXT_CHUNKS = 5
DEFAULT_CHUNK_SIZE = 800
DEFAULT_CHUNK_OVERLAP = 120
DEFAULT_MEMORY_ENABLED = True
DEFAULT_THEME = "system"

SUPPORTED_DOCUMENT_EXTENSIONS = frozenset({".pdf", ".docx", ".txt", ".md", ".markdown"})


def data_dir() -> Path:
    """Return the per-user application data directory."""
    path = Path(user_data_dir(APP_ID, ORG_NAME))
    path.mkdir(parents=True, exist_ok=True)
    return path


def config_dir() -> Path:
    """Return the per-user configuration directory."""
    path = Path(user_config_dir(APP_ID, ORG_NAME))
    path.mkdir(parents=True, exist_ok=True)
    return path


def log_dir() -> Path:
    """Return the per-user log directory."""
    path = Path(user_log_dir(APP_ID, ORG_NAME))
    path.mkdir(parents=True, exist_ok=True)
    return path


def database_path() -> Path:
    """Return the SQLite database path."""
    return data_dir() / "local_ai.db"


def documents_storage_dir() -> Path:
    """Return the directory where imported document copies are stored."""
    path = data_dir() / "documents"
    path.mkdir(parents=True, exist_ok=True)
    return path


def settings_path() -> Path:
    """Return the settings JSON file path."""
    return config_dir() / "settings.json"
