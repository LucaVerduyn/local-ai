"""Basic Qt smoke tests."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from local_ai.core.models import ThemeMode
from local_ai.ui.themes import apply_theme, resolve_theme
from local_ai.ui.views.home_view import HomeView


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app  # type: ignore[return-value]


def test_theme_resolve_light(qapp: QApplication) -> None:
    colors = resolve_theme(ThemeMode.LIGHT, qapp)
    assert colors.window.startswith("#")
    apply_theme(qapp, ThemeMode.DARK)
    apply_theme(qapp, ThemeMode.LIGHT)


def test_home_view_renders(qapp: QApplication, qtbot) -> None:  # type: ignore[no-untyped-def]
    view = HomeView()
    qtbot.addWidget(view)
    view.set_status("Online", "Ready")
    assert view.status_title.text() == "Online"
