"""Ollama models management view."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from local_ai.core.models import OllamaModelInfo
from local_ai.ui.widgets import EmptyState, PageHeader


def _format_size(size: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{size} B"


class ModelsView(QWidget):
    refresh_requested = Signal()
    pull_requested = Signal(str)
    delete_requested = Signal(str)
    set_chat_model = Signal(str)
    set_embedding_model = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(14)

        root.addWidget(
            PageHeader(
                "Models",
                "Manage Ollama models used for chat and embeddings. Everything stays local.",
            )
        )

        self.status = QLabel("Checking Ollama…")
        self.status.setWordWrap(True)
        root.addWidget(self.status)

        toolbar = QHBoxLayout()
        refresh = QPushButton("Refresh")
        refresh.setProperty("class", "Secondary")
        refresh.clicked.connect(self.refresh_requested.emit)
        toolbar.addWidget(refresh)
        toolbar.addStretch(1)
        root.addLayout(toolbar)

        self.list = QListWidget()
        root.addWidget(self.list, 1)

        self.empty = EmptyState(
            "No models found",
            "Pull a chat model such as qwen3:8b (recommended) or llama3.2 (faster), "
            "and an embedding model such as nomic-embed-text.",
        )
        root.addWidget(self.empty)

        pull_row = QHBoxLayout()
        self.pull_input = QLineEdit()
        self.pull_input.setPlaceholderText("Model name to pull, e.g. qwen3:8b")
        pull_btn = QPushButton("Pull model")
        pull_btn.setProperty("class", "Primary")
        pull_btn.clicked.connect(self._on_pull)
        pull_row.addWidget(self.pull_input, 1)
        pull_row.addWidget(pull_btn)
        root.addLayout(pull_row)

        actions = QHBoxLayout()
        chat_btn = QPushButton("Use as chat model")
        chat_btn.setProperty("class", "Secondary")
        chat_btn.clicked.connect(self._on_set_chat)
        embed_btn = QPushButton("Use as embedding model")
        embed_btn.setProperty("class", "Secondary")
        embed_btn.clicked.connect(self._on_set_embed)
        delete_btn = QPushButton("Delete")
        delete_btn.setProperty("class", "Danger")
        delete_btn.clicked.connect(self._on_delete)
        actions.addWidget(chat_btn)
        actions.addWidget(embed_btn)
        actions.addWidget(delete_btn)
        actions.addStretch(1)
        root.addLayout(actions)

        self.progress = QLabel("")
        self.progress.setProperty("class", "Muted")
        root.addWidget(self.progress)

    def set_connection_status(self, available: bool, detail: str) -> None:
        prefix = "Connected" if available else "Offline"
        self.status.setText(f"Ollama: {prefix} — {detail}")

    def set_models(
        self, models: list[OllamaModelInfo], chat_model: str, embedding_model: str
    ) -> None:
        self.list.clear()
        self.empty.setVisible(not models)
        self.list.setVisible(bool(models))
        for model in models:
            markers: list[str] = []
            if model.name == chat_model or model.name.startswith(f"{chat_model}:"):
                markers.append("chat")
            if model.name == embedding_model or model.name.startswith(f"{embedding_model}:"):
                markers.append("embedding")
            marker = f" [{', '.join(markers)}]" if markers else ""
            item = QListWidgetItem(f"{model.name}{marker}  ·  {_format_size(model.size)}")
            item.setData(Qt.ItemDataRole.UserRole, model.name)
            item.setToolTip(f"Digest: {model.digest}\nModified: {model.modified_at}")
            self.list.addItem(item)

    def set_progress(self, message: str) -> None:
        self.progress.setText(message)

    def _selected_name(self) -> str | None:
        item = self.list.currentItem()
        if item is None:
            return None
        return str(item.data(Qt.ItemDataRole.UserRole))

    def _on_pull(self) -> None:
        name = self.pull_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Pull model", "Enter a model name.")
            return
        self.pull_requested.emit(name)

    def _on_set_chat(self) -> None:
        name = self._selected_name()
        if name:
            self.set_chat_model.emit(name)

    def _on_set_embed(self) -> None:
        name = self._selected_name()
        if name:
            self.set_embedding_model.emit(name)

    def _on_delete(self) -> None:
        name = self._selected_name()
        if not name:
            return
        if (
            QMessageBox.question(self, "Delete model", f"Delete Ollama model '{name}'?")
            == QMessageBox.StandardButton.Yes
        ):
            self.delete_requested.emit(name)
