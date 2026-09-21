"""Documents management view."""

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

from local_ai.core.models import Document, DocumentStatus
from local_ai.ui.widgets import EmptyState, PageHeader


class DocumentsView(QWidget):
    import_requested = Signal()
    reindex_requested = Signal(int)
    delete_requested = Signal(int)
    search_changed = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(14)

        root.addWidget(
            PageHeader(
                "Documents",
                "Import local files and index them for private semantic search and RAG answers.",
            )
        )

        toolbar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search documents…")
        self.search.textChanged.connect(self.search_changed.emit)
        import_btn = QPushButton("Import files…")
        import_btn.setProperty("class", "Primary")
        import_btn.clicked.connect(self.import_requested.emit)
        toolbar.addWidget(self.search, 1)
        toolbar.addWidget(import_btn)
        root.addLayout(toolbar)

        self.list = QListWidget()
        self.list.currentItemChanged.connect(self._on_select)
        root.addWidget(self.list, 1)

        self.detail = QLabel("Select a document to see details.")
        self.detail.setWordWrap(True)
        self.detail.setProperty("class", "Muted")
        root.addWidget(self.detail)

        actions = QHBoxLayout()
        self.reindex_btn = QPushButton("Re-index")
        self.reindex_btn.setProperty("class", "Secondary")
        self.reindex_btn.clicked.connect(self._on_reindex)
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setProperty("class", "Danger")
        self.delete_btn.clicked.connect(self._on_delete)
        actions.addWidget(self.reindex_btn)
        actions.addWidget(self.delete_btn)
        actions.addStretch(1)
        root.addLayout(actions)

        self.empty = EmptyState(
            "No documents yet",
            "Import PDF, DOCX, TXT, or Markdown files. They are copied into Local AI storage and indexed locally.",
        )
        root.addWidget(self.empty)
        self._selected_id: int | None = None

    def set_documents(self, documents: list[Document]) -> None:
        self.list.clear()
        self.empty.setVisible(not documents)
        self.list.setVisible(bool(documents))
        for document in documents:
            item = QListWidgetItem(f"{document.title}  ·  {document.status.value}")
            item.setData(Qt.ItemDataRole.UserRole, document.id)
            tip = f"{document.filename}\n{document.chunk_count} chunks"
            if document.error_message:
                tip += f"\nError: {document.error_message}"
            item.setToolTip(tip)
            if document.status == DocumentStatus.ERROR:
                item.setForeground(Qt.GlobalColor.red)
            self.list.addItem(item)

    def show_document(self, document: Document | None) -> None:
        self._selected_id = document.id if document else None
        if document is None:
            self.detail.setText("Select a document to see details.")
            return
        error = f"\nError: {document.error_message}" if document.error_message else ""
        self.detail.setText(
            f"{document.title}\n"
            f"File: {document.filename} ({document.file_size:,} bytes)\n"
            f"Status: {document.status.value} · Chunks: {document.chunk_count}\n"
            f"Imported: {document.created_at:%Y-%m-%d %H:%M}{error}"
        )

    def set_busy(self, busy: bool, message: str = "") -> None:
        self.reindex_btn.setEnabled(not busy)
        self.delete_btn.setEnabled(not busy)
        if message:
            self.detail.setText(message)

    def _on_select(
        self, current: QListWidgetItem | None, _previous: QListWidgetItem | None
    ) -> None:
        if current is None:
            self.show_document(None)
            return
        self._selected_id = int(current.data(Qt.ItemDataRole.UserRole))

    def _on_reindex(self) -> None:
        if self._selected_id is not None:
            self.reindex_requested.emit(self._selected_id)

    def _on_delete(self) -> None:
        if self._selected_id is None:
            return
        answer = QMessageBox.question(
            self, "Delete document", "Delete this document and its index?"
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.delete_requested.emit(self._selected_id)
