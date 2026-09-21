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
    focus: str


LIGHT = ThemeColors(
    window="#F4F6F9",
    sidebar="#E9EEF4",
    surface="#FFFFFF",
    surface_alt="#F7F9FC",
    border="#D3DBE5",
    text="#152033",
    text_muted="#5A6A7C",
    accent="#0F6CBD",
    accent_hover="#0C5A9E",
    accent_text="#FFFFFF",
    danger="#B42318",
    success="#067647",
    input="#FFFFFF",
    chat_user="#DCEBFA",
    chat_assistant="#FFFFFF",
    focus="#0F6CBD",
)

DARK = ThemeColors(
    window="#0F141C",
    sidebar="#0B1017",
    surface="#171E28",
    surface_alt="#121821",
    border="#2A3544",
    text="#E8EEF6",
    text_muted="#96A4B5",
    accent="#3D8BFD",
    accent_hover="#2F78E0",
    accent_text="#06101F",
    danger="#F04438",
    success="#32D583",
    input="#0F151D",
    chat_user="#1A2F4A",
    chat_assistant="#171E28",
    focus="#3D8BFD",
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
        font-family: "Segoe UI Variable", "Segoe UI", "SF Pro Text", "Helvetica Neue", sans-serif;
        font-size: 13.5px;
        color: {c.text};
    }}
    #Sidebar {{
        background: {c.sidebar};
        border-right: 1px solid {c.border};
    }}
    #BrandLabel {{
        font-size: 19px;
        font-weight: 700;
        letter-spacing: -0.2px;
        color: {c.text};
        padding: 6px 10px 2px 10px;
    }}
    #BrandSub {{
        color: {c.text_muted};
        font-size: 11.5px;
        padding: 0 10px 14px 10px;
    }}
    #PageTitle {{
        font-size: 24px;
        font-weight: 700;
        letter-spacing: -0.3px;
    }}
    #PageSubtitle, QLabel[class="Muted"] {{
        color: {c.text_muted};
        font-size: 13px;
    }}
    #ChatTitle {{
        font-size: 18px;
        font-weight: 700;
    }}
    #ChatSidebarTitle {{
        font-size: 14px;
        font-weight: 650;
    }}
    #EmptyHeading {{
        font-size: 16px;
        font-weight: 650;
    }}
    #StatusChip {{
        background: {c.surface_alt};
        border: 1px solid {c.border};
        border-radius: 999px;
        padding: 4px 10px;
        color: {c.text_muted};
        font-size: 12px;
    }}
    #ComposerFrame {{
        background: {c.surface};
        border: 1px solid {c.border};
        border-radius: 14px;
    }}
    #MessageBubble[bubble="user"] {{
        background: {c.chat_user};
        border: 1px solid {c.border};
        border-radius: 14px;
    }}
    #MessageBubble[bubble="assistant"] {{
        background: {c.chat_assistant};
        border: 1px solid {c.border};
        border-radius: 14px;
    }}
    #BubbleRole {{
        font-weight: 650;
        font-size: 12px;
        color: {c.text_muted};
    }}
    #BubbleBody, #BubbleStream {{
        background: transparent;
        border: none;
        color: {c.text};
        font-size: 13.5px;
        line-height: 1.4;
    }}
    #BubbleSources {{
        color: {c.text_muted};
        font-size: 11.5px;
    }}
    QPushButton[class="NavButton"] {{
        text-align: left;
        padding: 11px 14px;
        border: none;
        border-radius: 10px;
        background: transparent;
        color: {c.text};
        font-weight: 550;
        min-height: 20px;
    }}
    QPushButton[class="NavButton"]:hover {{
        background: {c.surface};
    }}
    QPushButton[class="NavButton"][active="true"] {{
        background: {c.accent};
        color: {c.accent_text};
    }}
    QPushButton[class="NavButton"]:focus {{
        outline: none;
        border: 2px solid {c.focus};
    }}
    QPushButton[class="Primary"] {{
        background: {c.accent};
        color: {c.accent_text};
        border: none;
        border-radius: 10px;
        padding: 9px 16px;
        font-weight: 650;
        min-height: 20px;
    }}
    QPushButton[class="Primary"]:hover {{
        background: {c.accent_hover};
    }}
    QPushButton[class="Primary"]:disabled {{
        background: {c.border};
        color: {c.text_muted};
    }}
    QPushButton[class="Primary"]:focus {{
        outline: none;
        border: 2px solid {c.focus};
    }}
    QPushButton[class="Secondary"] {{
        background: {c.surface};
        color: {c.text};
        border: 1px solid {c.border};
        border-radius: 10px;
        padding: 9px 14px;
        min-height: 20px;
    }}
    QPushButton[class="Secondary"]:hover {{
        background: {c.surface_alt};
    }}
    QPushButton[class="Danger"] {{
        background: transparent;
        color: {c.danger};
        border: 1px solid {c.danger};
        border-radius: 10px;
        padding: 9px 14px;
        min-height: 20px;
    }}
    QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
        background: {c.input};
        border: 1px solid {c.border};
        border-radius: 10px;
        padding: 9px 11px;
        selection-background-color: {c.accent};
    }}
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus {{
        border: 2px solid {c.focus};
        padding: 8px 10px;
    }}
    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}
    QListWidget, QTreeWidget, QTableWidget {{
        background: {c.surface};
        border: 1px solid {c.border};
        border-radius: 12px;
        outline: none;
        padding: 4px;
    }}
    QListWidget::item {{
        padding: 11px 12px;
        border-radius: 8px;
        margin: 1px 0;
    }}
    QListWidget::item:selected {{
        background: {c.accent};
        color: {c.accent_text};
    }}
    QListWidget::item:hover:!selected {{
        background: {c.surface_alt};
    }}
    QScrollArea {{
        border: none;
        background: transparent;
    }}
    QFrame[class="Card"] {{
        background: {c.surface};
        border: 1px solid {c.border};
        border-radius: 14px;
    }}
    QLabel[class="Title"] {{
        font-size: 22px;
        font-weight: 700;
    }}
    QLabel[class="SectionTitle"] {{
        font-size: 16px;
        font-weight: 650;
    }}
    QStatusBar {{
        background: {c.surface};
        border-top: 1px solid {c.border};
        color: {c.text_muted};
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
        color: {c.text};
    }}
    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border-radius: 4px;
        border: 1px solid {c.border};
        background: {c.input};
    }}
    QCheckBox::indicator:checked {{
        background: {c.accent};
        border-color: {c.accent};
    }}
    QToolTip {{
        background: {c.surface};
        color: {c.text};
        border: 1px solid {c.border};
        padding: 8px;
        border-radius: 8px;
    }}
    """
