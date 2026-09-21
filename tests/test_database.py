"""Database and settings tests."""

from __future__ import annotations

from pathlib import Path

from local_ai.core.database import Database
from local_ai.core.migrations import CURRENT_SCHEMA_VERSION
from local_ai.core.models import ThemeMode
from local_ai.core.settings import SettingsStore


def test_migrations_apply(tmp_path: Path) -> None:
    db = Database(tmp_path / "db.sqlite")
    db.migrate()
    row = db.fetchone("SELECT MAX(version) AS v FROM schema_migrations")
    assert row is not None
    assert int(row["v"]) == CURRENT_SCHEMA_VERSION
    tables = {r["name"] for r in db.fetchall("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "conversations" in tables
    assert "documents" in tables
    assert "memory_items" in tables
    db.close()


def test_settings_roundtrip(tmp_path: Path) -> None:
    store = SettingsStore(tmp_path / "settings.json")
    updated = store.update(theme=ThemeMode.DARK, temperature=0.2, chat_model="mistral")
    assert updated.theme == ThemeMode.DARK
    assert updated.temperature == 0.2
    assert updated.chat_model == "mistral"

    reloaded = SettingsStore(tmp_path / "settings.json")
    assert reloaded.settings.theme == ThemeMode.DARK
    assert reloaded.settings.chat_model == "mistral"
