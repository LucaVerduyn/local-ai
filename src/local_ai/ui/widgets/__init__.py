"""Reusable UI widgets."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from local_ai.core.models import Citation, Message, MessageRole


class PageHeader(QWidget):
    def __init__(self, title: str, subtitle: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 16)
        layout.setSpacing(6)
        title_label = QLabel(title)
        title_label.setObjectName("PageTitle")
        layout.addWidget(title_label)
        if subtitle:
            sub = QLabel(subtitle)
            sub.setObjectName("PageSubtitle")
            sub.setWordWrap(True)
            layout.addWidget(sub)


class EmptyState(QFrame):
    def __init__(self, title: str, body: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("class", "Card")
        self.setObjectName("EmptyState")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 40, 32, 40)
        layout.setSpacing(10)
        heading = QLabel(title)
        heading.setObjectName("EmptyHeading")
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text = QLabel(body)
        text.setWordWrap(True)
        text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text.setProperty("class", "Muted")
        layout.addWidget(heading)
        layout.addWidget(text)


class ComposerEdit(QTextEdit):
    """Chat composer: Enter sends, Shift+Enter inserts a newline."""

    submit_requested = Signal()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                super().keyPressEvent(event)
                return
            self.submit_requested.emit()
            return
        super().keyPressEvent(event)


class MessageBubble(QFrame):
    def __init__(self, message: Message, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.NoFrame)
        is_user = message.role == MessageRole.USER
        self.setProperty("bubble", "user" if is_user else "assistant")
        self.setObjectName("MessageBubble")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        role = QLabel("You" if is_user else "Local AI")
        role.setObjectName("BubbleRole")
        layout.addWidget(role)

        body = QTextBrowser()
        body.setObjectName("BubbleBody")
        body.setOpenExternalLinks(False)
        body.setFrameShape(QFrame.Shape.NoFrame)
        body.setMarkdown(message.content)
        body.setMinimumHeight(36)
        body.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        body.document().setDocumentMargin(0)
        body.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout.addWidget(body)

        if message.sources:
            sources = QLabel(self._format_sources(message.sources))
            sources.setObjectName("BubbleSources")
            sources.setWordWrap(True)
            layout.addWidget(sources)

    @staticmethod
    def _format_sources(citations: list[Citation]) -> str:
        parts = ["Sources"]
        for citation in citations[:5]:
            parts.append(f"• {citation.document_title} ({citation.score:.0%})")
        return "\n".join(parts)


class StreamingBubble(QFrame):
    """Bubble that accumulates streamed assistant tokens."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("MessageBubble")
        self.setProperty("bubble", "assistant")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)
        role = QLabel("Local AI")
        role.setObjectName("BubbleRole")
        self.body = QLabel("Thinking…")
        self.body.setObjectName("BubbleStream")
        self.body.setWordWrap(True)
        self.body.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(role)
        layout.addWidget(self.body)
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
