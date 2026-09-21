"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from local_ai.core.database import Database
from local_ai.core.settings import SettingsStore
from local_ai.services.embedding_service import EmbeddingService
from tests.fakes import FakeOllama


@pytest.fixture
def tmp_db(tmp_path: Path) -> Database:
    db = Database(tmp_path / "test.db")
    db.migrate()
    yield db
    db.close()


@pytest.fixture
def settings(tmp_path: Path) -> SettingsStore:
    return SettingsStore(tmp_path / "settings.json")


@pytest.fixture
def fake_ollama() -> FakeOllama:
    return FakeOllama()


@pytest.fixture
def embedding(fake_ollama: FakeOllama) -> EmbeddingService:
    return EmbeddingService(fake_ollama, "nomic-embed-text")
