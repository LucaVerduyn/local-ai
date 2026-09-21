"""Home dashboard view."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from local_ai.ui.widgets import PageHeader


class HomeView(QWidget):
    open_chat = Signal()
    open_documents = Signal()
    open_models = Signal()
    open_settings = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(20)

        root.addWidget(
            PageHeader(
                "Local AI",
                "Private desktop AI. Chat, documents, and memory — all on your machine.",
            )
        )

        grid = QGridLayout()
        grid.setSpacing(14)
        cards = [
            ("Chat", "Talk with local models via Ollama, with streaming replies.", self.open_chat),
            (
                "Documents",
                "Import PDFs, Word, Markdown, and text for private RAG Q&A.",
                self.open_documents,
            ),
            (
                "Models",
                "Inspect and manage Ollama models installed on this device.",
                self.open_models,
            ),
            ("Settings", "Theme, models, retrieval, and privacy preferences.", self.open_settings),
        ]
        for index, (title, body, signal) in enumerate(cards):
            card = self._make_card(title, body, signal)
            grid.addWidget(card, index // 2, index % 2)
        root.addLayout(grid)

        status = QFrame()
        status.setProperty("class", "Card")
        status_layout = QVBoxLayout(status)
        status_layout.setContentsMargins(18, 16, 18, 16)
        self.status_title = QLabel("Getting started")
        self.status_title.setStyleSheet("font-weight: 600; font-size: 15px;")
        self.status_body = QLabel(
            "Install and run Ollama, pull a chat model and an embedding model, then start chatting."
        )
        self.status_body.setWordWrap(True)
        self.status_body.setProperty("class", "Muted")
        status_layout.addWidget(self.status_title)
        status_layout.addWidget(self.status_body)
        root.addWidget(status)
        root.addStretch(1)

        actions = QHBoxLayout()
        start = QPushButton("Start chatting")
        start.setProperty("class", "Primary")
        start.clicked.connect(self.open_chat.emit)
        docs = QPushButton("Import documents")
        docs.setProperty("class", "Secondary")
        docs.clicked.connect(self.open_documents.emit)
        actions.addWidget(start)
        actions.addWidget(docs)
        actions.addStretch(1)
        root.addLayout(actions)

    def _make_card(self, title: str, body: str, signal: Signal) -> QFrame:
        frame = QFrame()
        frame.setProperty("class", "Card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(18, 16, 18, 16)
        heading = QLabel(title)
        heading.setStyleSheet("font-size: 15px; font-weight: 600;")
        text = QLabel(body)
        text.setWordWrap(True)
        text.setProperty("class", "Muted")
        button = QPushButton(f"Open {title}")
        button.setProperty("class", "Secondary")
        button.clicked.connect(signal.emit)
        layout.addWidget(heading)
        layout.addWidget(text)
        layout.addStretch(1)
        layout.addWidget(button)
        return frame

    def set_status(self, title: str, body: str) -> None:
        self.status_title.setText(title)
        self.status_body.setText(body)
