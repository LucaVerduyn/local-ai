"""Reusable UI widgets."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from local_ai.core.models import Citation, Message, MessageRole


class PageHeader(QWidget):
    def __init__(self, title: str, subtitle: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 12)
        layout.setSpacing(4)
        title_label = QLabel(title)
        title_label.setProperty("class", "Title")
        title_label.setObjectName("PageTitle")
        title_label.setStyleSheet("font-size: 22px; font-weight: 700;")
        layout.addWidget(title_label)
        if subtitle:
            sub = QLabel(subtitle)
            sub.setProperty("class", "Muted")
            sub.setObjectName("PageSubtitle")
            sub.setWordWrap(True)
            layout.addWidget(sub)


class EmptyState(QFrame):
    def __init__(self, title: str, body: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("class", "Card")
        self.setObjectName("EmptyState")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 36, 28, 36)
        layout.setSpacing(8)
        heading = QLabel(title)
        heading.setStyleSheet("font-size: 16px; font-weight: 600;")
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text = QLabel(body)
        text.setWordWrap(True)
        text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text.setProperty("class", "Muted")
        layout.addWidget(heading)
        layout.addWidget(text)


class MessageBubble(QFrame):
    def __init__(self, message: Message, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.NoFrame)
        is_user = message.role == MessageRole.USER
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        role = QLabel("You" if is_user else "Local AI")
        role.setStyleSheet("font-weight: 600; font-size: 12px;")
        layout.addWidget(role)

        body = QTextBrowser()
        body.setOpenExternalLinks(False)
        body.setFrameShape(QFrame.Shape.NoFrame)
        body.setMarkdown(message.content)
        body.setMinimumHeight(40)
        body.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        body.document().setDocumentMargin(0)
        layout.addWidget(body)

        if message.sources:
            sources = QLabel(self._format_sources(message.sources))
            sources.setWordWrap(True)
            sources.setStyleSheet("font-size: 11px; opacity: 0.85;")
            layout.addWidget(sources)

        bg = "#E7F0FF" if is_user else "transparent"
        border = "1px solid #D5DBE3"
        self.setStyleSheet(
            f"""
            MessageBubble {{
                background: {bg};
                border: {border};
                border-radius: 12px;
            }}
            """
        )

    @staticmethod
    def _format_sources(citations: list[Citation]) -> str:
        parts = ["Sources:"]
        for citation in citations[:5]:
            parts.append(f"• {citation.document_title} ({citation.score:.0%})")
        return "\n".join(parts)


class StreamingBubble(QFrame):
    """Bubble that accumulates streamed assistant tokens."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        role = QLabel("Local AI")
        role.setStyleSheet("font-weight: 600; font-size: 12px;")
        self.body = QLabel("")
        self.body.setWordWrap(True)
        self.body.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(role)
        layout.addWidget(self.body)
        self.setStyleSheet(
            """
            StreamingBubble {
                background: transparent;
                border: 1px solid #D5DBE3;
                border-radius: 12px;
            }
            """
        )
        self._text = ""

    def append_token(self, token: str) -> None:
        self._text += token
        self.body.setText(self._text)

    def text(self) -> str:
        return self._text


class ActionBar(QWidget):
    primary_clicked = Signal()
    secondary_clicked = Signal()

    def __init__(
        self,
        primary: str,
        secondary: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch(1)
        if secondary:
            sec = QPushButton(secondary)
            sec.setProperty("class", "Secondary")
            sec.clicked.connect(self.secondary_clicked.emit)
            layout.addWidget(sec)
        prim = QPushButton(primary)
        prim.setProperty("class", "Primary")
        prim.clicked.connect(self.primary_clicked.emit)
        layout.addWidget(prim)
        self.primary_button = prim
