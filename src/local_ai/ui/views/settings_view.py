"""Application settings view."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from local_ai.core.models import AppSettings, ThemeMode
from local_ai.ui.widgets import PageHeader


class SettingsView(QWidget):
    save_requested = Signal(dict)
    reset_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(14)

        root.addWidget(
            PageHeader(
                "Settings",
                "Configure Ollama, retrieval, theme, and privacy defaults. No accounts or cloud sync.",
            )
        )

        form = QFormLayout()
        form.setSpacing(10)

        self.ollama_url = QLineEdit()
        self.chat_model = QLineEdit()
        self.embedding_model = QLineEdit()
        self.temperature = QDoubleSpinBox()
        self.temperature.setRange(0.0, 2.0)
        self.temperature.setSingleStep(0.1)
        self.context_chunks = QSpinBox()
        self.context_chunks.setRange(1, 20)
        self.chunk_size = QSpinBox()
        self.chunk_size.setRange(200, 4000)
        self.chunk_size.setSingleStep(50)
        self.chunk_overlap = QSpinBox()
        self.chunk_overlap.setRange(0, 1000)
        self.chunk_overlap.setSingleStep(20)
        self.theme = QComboBox()
        self.theme.addItem("System", ThemeMode.SYSTEM.value)
        self.theme.addItem("Light", ThemeMode.LIGHT.value)
        self.theme.addItem("Dark", ThemeMode.DARK.value)
        self.memory_enabled = QComboBox()
        self.memory_enabled.addItem("Enabled", True)
        self.memory_enabled.addItem("Disabled", False)
        self.system_prompt = QTextEdit()
        self.system_prompt.setFixedHeight(140)

        form.addRow("Ollama URL", self.ollama_url)
        form.addRow("Chat model", self.chat_model)
        form.addRow("Embedding model", self.embedding_model)
        form.addRow("Temperature", self.temperature)
        form.addRow("RAG context chunks", self.context_chunks)
        form.addRow("Chunk size", self.chunk_size)
        form.addRow("Chunk overlap", self.chunk_overlap)
        form.addRow("Theme", self.theme)
        form.addRow("Persistent memory", self.memory_enabled)
        form.addRow("System prompt", self.system_prompt)
        root.addLayout(form)

        note = QLabel(
            "Local AI never sends your chats, documents, or memories to a remote service. "
            "All inference goes to the Ollama instance you configure (default: localhost)."
        )
        note.setWordWrap(True)
        note.setProperty("class", "Muted")
        root.addWidget(note)

        actions = QHBoxLayout()
        save = QPushButton("Save settings")
        save.setProperty("class", "Primary")
        save.clicked.connect(self._on_save)
        reset = QPushButton("Reload")
        reset.setProperty("class", "Secondary")
        reset.clicked.connect(self.reset_requested.emit)
        actions.addWidget(save)
        actions.addWidget(reset)
        actions.addStretch(1)
        root.addLayout(actions)
        root.addStretch(1)

    def load_settings(self, settings: AppSettings) -> None:
        self.ollama_url.setText(settings.ollama_base_url)
        self.chat_model.setText(settings.chat_model)
        self.embedding_model.setText(settings.embedding_model)
        self.temperature.setValue(settings.temperature)
        self.context_chunks.setValue(settings.context_chunks)
        self.chunk_size.setValue(settings.chunk_size)
        self.chunk_overlap.setValue(settings.chunk_overlap)
        index = self.theme.findData(settings.theme.value)
        if index >= 0:
            self.theme.setCurrentIndex(index)
        mem_index = self.memory_enabled.findData(settings.memory_enabled)
        if mem_index >= 0:
            self.memory_enabled.setCurrentIndex(mem_index)
        self.system_prompt.setPlainText(settings.system_prompt)

    def _on_save(self) -> None:
        payload = {
            "ollama_base_url": self.ollama_url.text().strip(),
            "chat_model": self.chat_model.text().strip(),
            "embedding_model": self.embedding_model.text().strip(),
            "temperature": self.temperature.value(),
            "context_chunks": self.context_chunks.value(),
            "chunk_size": self.chunk_size.value(),
            "chunk_overlap": self.chunk_overlap.value(),
            "theme": self.theme.currentData(),
            "memory_enabled": self.memory_enabled.currentData(),
            "system_prompt": self.system_prompt.toPlainText().strip(),
        }
        self.save_requested.emit(payload)
