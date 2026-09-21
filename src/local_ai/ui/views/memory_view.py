"""Memory management view."""

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
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from local_ai.core.models import MemoryItem
from local_ai.ui.widgets import EmptyState, PageHeader


class MemoryView(QWidget):
    add_requested = Signal(str, str, int)
    delete_requested = Signal(int)
    search_changed = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(14)

        root.addWidget(
            PageHeader(
                "Memory",
                "Optional persistent notes the assistant can recall. Stored only on this device.",
            )
        )

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search memory…")
        self.search.textChanged.connect(self.search_changed.emit)
        root.addWidget(self.search)

        self.list = QListWidget()
        root.addWidget(self.list, 1)

        self.empty = EmptyState(
            "No memories yet",
            "Add facts, preferences, or project notes. Disable memory anytime in Settings or per chat.",
        )
        root.addWidget(self.empty)

        form = QVBoxLayout()
        form.addWidget(QLabel("New memory"))
        self.content = QTextEdit()
        self.content.setPlaceholderText("e.g. Prefers concise answers and Python examples.")
        self.content.setFixedHeight(80)
        form.addWidget(self.content)

        meta = QHBoxLayout()
        self.tags = QLineEdit()
        self.tags.setPlaceholderText("Tags (optional)")
        self.importance = QSpinBox()
        self.importance.setRange(1, 5)
        self.importance.setValue(1)
        self.importance.setPrefix("Importance ")
        meta.addWidget(self.tags, 1)
        meta.addWidget(self.importance)
        form.addLayout(meta)

        actions = QHBoxLayout()
        add_btn = QPushButton("Add memory")
        add_btn.setProperty("class", "Primary")
        add_btn.clicked.connect(self._on_add)
        delete_btn = QPushButton("Delete selected")
        delete_btn.setProperty("class", "Danger")
        delete_btn.clicked.connect(self._on_delete)
        actions.addWidget(add_btn)
        actions.addWidget(delete_btn)
        actions.addStretch(1)
        form.addLayout(actions)
        root.addLayout(form)

    def set_items(self, items: list[MemoryItem]) -> None:
        self.list.clear()
        self.empty.setVisible(not items)
        self.list.setVisible(bool(items))
        for item in items:
            label = item.content if len(item.content) < 120 else item.content[:117] + "…"
            row = QListWidgetItem(label)
            row.setData(Qt.ItemDataRole.UserRole, item.id)
            tip = item.content
            if item.tags:
                tip += f"\nTags: {item.tags}"
            tip += f"\nImportance: {item.importance}"
            row.setToolTip(tip)
            self.list.addItem(row)

    def _on_add(self) -> None:
        content = self.content.toPlainText().strip()
        if not content:
            QMessageBox.warning(self, "Memory", "Enter memory content first.")
            return
        self.add_requested.emit(content, self.tags.text().strip(), self.importance.value())
        self.content.clear()
        self.tags.clear()
        self.importance.setValue(1)

    def _on_delete(self) -> None:
        item = self.list.currentItem()
        if item is None:
            return
        memory_id = int(item.data(Qt.ItemDataRole.UserRole))
        if (
            QMessageBox.question(self, "Delete memory", "Delete this memory?")
            == QMessageBox.StandardButton.Yes
        ):
            self.delete_requested.emit(memory_id)
