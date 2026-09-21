"""Persistent application settings."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

from local_ai.config import (
    DEFAULT_CHAT_MODEL,
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CONTEXT_CHUNKS,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_MEMORY_ENABLED,
    DEFAULT_OLLAMA_BASE_URL,
    DEFAULT_TEMPERATURE,
    DEFAULT_THEME,
    settings_path,
)
from local_ai.core.models import AppSettings, ThemeMode

logger = logging.getLogger(__name__)

DEFAULT_SYSTEM_PROMPT = (
    "You are Local AI, a helpful private assistant running entirely on the user's machine. "
    "Be accurate, concise, and clear. When document context is provided, ground answers in "
    "that context and cite sources by document title. If you are unsure, say so."
)


class SettingsModel(BaseModel):
    ollama_base_url: str = DEFAULT_OLLAMA_BASE_URL
    chat_model: str = DEFAULT_CHAT_MODEL
    embedding_model: str = DEFAULT_EMBEDDING_MODEL
    temperature: float = Field(default=DEFAULT_TEMPERATURE, ge=0.0, le=2.0)
    context_chunks: int = Field(default=DEFAULT_CONTEXT_CHUNKS, ge=1, le=20)
    chunk_size: int = Field(default=DEFAULT_CHUNK_SIZE, ge=200, le=4000)
    chunk_overlap: int = Field(default=DEFAULT_CHUNK_OVERLAP, ge=0, le=1000)
    memory_enabled: bool = DEFAULT_MEMORY_ENABLED
    theme: ThemeMode = ThemeMode(DEFAULT_THEME)
    system_prompt: str = DEFAULT_SYSTEM_PROMPT

    @field_validator("ollama_base_url")
    @classmethod
    def strip_trailing_slash(cls, value: str) -> str:
        return value.rstrip("/")

    def to_app_settings(self) -> AppSettings:
        return AppSettings(
            ollama_base_url=self.ollama_base_url,
            chat_model=self.chat_model,
            embedding_model=self.embedding_model,
            temperature=self.temperature,
            context_chunks=self.context_chunks,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            memory_enabled=self.memory_enabled,
            theme=self.theme,
            system_prompt=self.system_prompt,
        )


class SettingsStore:
    """Load and save application settings as JSON."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or settings_path()
        self._model = self._load()

    @property
    def settings(self) -> AppSettings:
        return self._model.to_app_settings()

    def _load(self) -> SettingsModel:
        if not self.path.exists():
            model = SettingsModel()
            self._write(model)
            return model
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            return SettingsModel.model_validate(raw)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            logger.warning("Failed to load settings, using defaults: %s", exc)
            return SettingsModel()

    def _write(self, model: SettingsModel) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(model.model_dump_json(indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def update(self, **kwargs: object) -> AppSettings:
        data = self._model.model_dump()
        data.update(kwargs)
        self._model = SettingsModel.model_validate(data)
        self._write(self._model)
        return self.settings

    def reload(self) -> AppSettings:
        self._model = self._load()
        return self.settings
