"""Theme palettes and QSS generation."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from local_ai.core.models import ThemeMode


@dataclass(frozen=True, slots=True)
class ThemeColors:
    window: str
    sidebar: str
    surface: str
    surface_alt: str
    border: str
    text: str
    text_muted: str
    accent: str
    accent_hover: str
    accent_text: str
    danger: str
    success: str
    input: str
    chat_user: str
    chat_assistant: str


LIGHT = ThemeColors(
    window="#F3F5F8",
    sidebar="#E8ECF1",
    surface="#FFFFFF",
    surface_alt="#F7F9FC",
    border="#D5DBE3",
    text="#1A2332",
    text_muted="#5C6B7A",
    accent="#1F6FEB",
    accent_hover="#1A5CC7",
    accent_text="#FFFFFF",
    danger="#C62828",
    success="#2E7D32",
    input="#FFFFFF",
    chat_user="#E7F0FF",
    chat_assistant="#FFFFFF",
)

DARK = ThemeColors(
    window="#12171F",
    sidebar="#0E131A",
    surface="#1A222D",
    surface_alt="#151C26",
    border="#2A3442",
    text="#E8EEF5",
    text_muted="#9AA8B6",
    accent="#4C8DFF",
    accent_hover="#3B7AF0",
    accent_text="#0B1220",
    danger="#EF5350",
    success="#66BB6A",
    input="#121820",
    chat_user="#1B2A44",
    chat_assistant="#1A222D",
)


def resolve_theme(mode: ThemeMode, app: QApplication | None = None) -> ThemeColors:
    if mode == ThemeMode.LIGHT:
        return LIGHT
    if mode == ThemeMode.DARK:
        return DARK
    application = app or QApplication.instance()
    if isinstance(application, QApplication):
        lightness = application.palette().color(QPalette.ColorRole.Window).lightness()
        return LIGHT if lightness > 128 else DARK
    return LIGHT


def apply_theme(app: QApplication, mode: ThemeMode) -> ThemeColors:
    colors = resolve_theme(mode, app)
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(colors.window))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(colors.text))
    palette.setColor(QPalette.ColorRole.Base, QColor(colors.input))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(colors.surface_alt))
    palette.setColor(QPalette.ColorRole.Text, QColor(colors.text))
    palette.setColor(QPalette.ColorRole.Button, QColor(colors.surface))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(colors.text))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(colors.accent))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(colors.accent_text))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(colors.surface))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(colors.text))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(colors.text_muted))
    app.setPalette(palette)
    app.setStyleSheet(build_stylesheet(colors))
    return colors


def build_stylesheet(c: ThemeColors) -> str:
    return f"""
    QMainWindow, QDialog {{
        background: {c.window};
        color: {c.text};
    }}
    QWidget {{
        font-family: "Segoe UI", "SF Pro Text", "Helvetica Neue", sans-serif;
        font-size: 13px;
        color: {c.text};
    }}
    #Sidebar {{
        background: {c.sidebar};
        border-right: 1px solid {c.border};
    }}
    #BrandLabel {{
        font-size: 18px;
        font-weight: 700;
        letter-spacing: 0.2px;
        color: {c.text};
        padding: 4px 8px;
    }}
    #BrandSub {{
        color: {c.text_muted};
        font-size: 11px;
        padding: 0 8px 12px 8px;
    }}
    QPushButton[class="NavButton"] {{
        text-align: left;
        padding: 10px 14px;
        border: none;
        border-radius: 8px;
        background: transparent;
        color: {c.text};
        font-weight: 500;
    }}
    QPushButton[class="NavButton"]:hover {{
        background: {c.surface};
    }}
    QPushButton[class="NavButton"][active="true"] {{
        background: {c.accent};
        color: {c.accent_text};
    }}
    QPushButton[class="Primary"] {{
        background: {c.accent};
        color: {c.accent_text};
        border: none;
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 600;
    }}
    QPushButton[class="Primary"]:hover {{
        background: {c.accent_hover};
    }}
    QPushButton[class="Primary"]:disabled {{
        background: {c.border};
        color: {c.text_muted};
    }}
    QPushButton[class="Secondary"] {{
        background: {c.surface};
        color: {c.text};
        border: 1px solid {c.border};
        border-radius: 8px;
        padding: 8px 14px;
    }}
    QPushButton[class="Secondary"]:hover {{
        background: {c.surface_alt};
    }}
    QPushButton[class="Danger"] {{
        background: transparent;
        color: {c.danger};
        border: 1px solid {c.danger};
        border-radius: 8px;
        padding: 8px 14px;
    }}
    QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
        background: {c.input};
        border: 1px solid {c.border};
        border-radius: 8px;
        padding: 8px 10px;
        selection-background-color: {c.accent};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}
    QListWidget, QTreeWidget, QTableWidget {{
        background: {c.surface};
        border: 1px solid {c.border};
        border-radius: 10px;
        outline: none;
    }}
    QListWidget::item {{
        padding: 10px 12px;
        border-bottom: 1px solid {c.border};
    }}
    QListWidget::item:selected {{
        background: {c.accent};
        color: {c.accent_text};
    }}
    QScrollArea {{
        border: none;
        background: transparent;
    }}
    QFrame[class="Card"] {{
        background: {c.surface};
        border: 1px solid {c.border};
        border-radius: 12px;
    }}
    QLabel[class="Muted"] {{
        color: {c.text_muted};
    }}
    QLabel[class="Title"] {{
        font-size: 22px;
        font-weight: 700;
    }}
    QLabel[class="SectionTitle"] {{
        font-size: 16px;
        font-weight: 600;
    }}
    QStatusBar {{
        background: {c.surface};
        border-top: 1px solid {c.border};
    }}
    QSplitter::handle {{
        background: {c.border};
        width: 1px;
    }}
    QProgressBar {{
        border: 1px solid {c.border};
        border-radius: 6px;
        text-align: center;
        background: {c.surface_alt};
    }}
    QProgressBar::chunk {{
        background: {c.accent};
        border-radius: 5px;
    }}
    QCheckBox {{
        spacing: 8px;
    }}
    QToolTip {{
        background: {c.surface};
        color: {c.text};
        border: 1px solid {c.border};
        padding: 6px;
    }}
    """
