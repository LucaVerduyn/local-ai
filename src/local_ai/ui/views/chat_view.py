"""Chat view with streaming, cancellation, and conversation history."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from local_ai.core.models import Conversation, Message
from local_ai.ui.widgets import EmptyState, MessageBubble, StreamingBubble


class ChatView(QWidget):
    new_chat = Signal()
    select_conversation = Signal(int)
    delete_conversation = Signal(int)
    send_message = Signal(str)
    cancel_generation = Signal()
    search_changed = Signal(str)
    flags_changed = Signal(bool, bool)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._streaming: StreamingBubble | None = None
        self._current_id: int | None = None

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        root.addWidget(splitter)

        # Sidebar history
        side = QWidget()
        side_layout = QVBoxLayout(side)
        side_layout.setContentsMargins(16, 16, 12, 16)
        side_layout.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel("Conversations")
        title.setStyleSheet("font-weight: 600; font-size: 14px;")
        new_btn = QPushButton("New")
        new_btn.setProperty("class", "Primary")
        new_btn.clicked.connect(self.new_chat.emit)
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(new_btn)
        side_layout.addLayout(header)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search conversations…")
        self.search.textChanged.connect(self.search_changed.emit)
        side_layout.addWidget(self.search)

        self.conversation_list = QListWidget()
        self.conversation_list.currentItemChanged.connect(self._on_select)
        side_layout.addWidget(self.conversation_list, 1)

        delete_btn = QPushButton("Delete selected")
        delete_btn.setProperty("class", "Danger")
        delete_btn.clicked.connect(self._on_delete)
        side_layout.addWidget(delete_btn)
        splitter.addWidget(side)

        # Main chat area
        main = QWidget()
        main_layout = QVBoxLayout(main)
        main_layout.setContentsMargins(16, 16, 20, 16)
        main_layout.setSpacing(10)

        top = QHBoxLayout()
        self.chat_title = QLabel("Chat")
        self.chat_title.setStyleSheet("font-size: 18px; font-weight: 700;")
        self.use_docs = QCheckBox("Use documents")
        self.use_docs.setChecked(True)
        self.use_memory = QCheckBox("Use memory")
        self.use_memory.setChecked(True)
        self.use_docs.stateChanged.connect(self._emit_flags)
        self.use_memory.stateChanged.connect(self._emit_flags)
        top.addWidget(self.chat_title)
        top.addStretch(1)
        top.addWidget(self.use_docs)
        top.addWidget(self.use_memory)
        main_layout.addLayout(top)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.messages_host = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_host)
        self.messages_layout.setContentsMargins(4, 4, 4, 4)
        self.messages_layout.setSpacing(12)
        self.messages_layout.addStretch(1)
        self.scroll_area.setWidget(self.messages_host)
        main_layout.addWidget(self.scroll_area, 1)

        self.empty = EmptyState(
            "Start a conversation",
            "Ask anything. Answers stay on this device. Enable documents to ground replies in your files.",
        )
        main_layout.addWidget(self.empty)

        composer = QHBoxLayout()
        self.input = QTextEdit()
        self.input.setPlaceholderText("Message Local AI…")
        self.input.setFixedHeight(84)
        self.send_btn = QPushButton("Send")
        self.send_btn.setProperty("class", "Primary")
        self.send_btn.setFixedHeight(84)
        self.send_btn.clicked.connect(self._on_send)
        self.cancel_btn = QPushButton("Stop")
        self.cancel_btn.setProperty("class", "Danger")
        self.cancel_btn.setFixedHeight(84)
        self.cancel_btn.setVisible(False)
        self.cancel_btn.clicked.connect(self.cancel_generation.emit)
        composer.addWidget(self.input, 1)
        composer.addWidget(self.send_btn)
        composer.addWidget(self.cancel_btn)
        main_layout.addLayout(composer)

        splitter.addWidget(main)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([280, 720])

    def set_conversations(self, conversations: list[Conversation], selected_id: int | None) -> None:
        self.conversation_list.blockSignals(True)
        self.conversation_list.clear()
        for conversation in conversations:
            item = QListWidgetItem(conversation.title)
            item.setData(Qt.ItemDataRole.UserRole, conversation.id)
            item.setToolTip(
                f"{conversation.model}\nUpdated {conversation.updated_at:%Y-%m-%d %H:%M}"
            )
            self.conversation_list.addItem(item)
            if selected_id is not None and conversation.id == selected_id:
                self.conversation_list.setCurrentItem(item)
        self.conversation_list.blockSignals(False)

    def show_conversation(self, conversation: Conversation | None, messages: list[Message]) -> None:
        self._clear_messages()
        self._streaming = None
        if conversation is None:
            self._current_id = None
            self.chat_title.setText("Chat")
            self.empty.setVisible(True)
            self.scroll_area.setVisible(False)
            return

        self._current_id = conversation.id
        self.chat_title.setText(conversation.title)
        self.use_docs.blockSignals(True)
        self.use_memory.blockSignals(True)
        self.use_docs.setChecked(conversation.use_documents)
        self.use_memory.setChecked(conversation.use_memory)
        self.use_docs.blockSignals(False)
        self.use_memory.blockSignals(False)

        self.empty.setVisible(False)
        self.scroll_area.setVisible(True)
        for message in messages:
            bubble = MessageBubble(message)
            self.messages_layout.insertWidget(self.messages_layout.count() - 1, bubble)
        self._scroll_to_bottom()

    def begin_streaming(self) -> None:
        self._streaming = StreamingBubble()
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, self._streaming)
        self.set_generating(True)
        self.empty.setVisible(False)
        self.scroll_area.setVisible(True)
        self._scroll_to_bottom()

    def append_token(self, token: str) -> None:
        if self._streaming is None:
            self.begin_streaming()
        assert self._streaming is not None
        self._streaming.append_token(token)
        self._scroll_to_bottom()

    def end_streaming(self) -> None:
        self.set_generating(False)
        self._streaming = None

    def set_generating(self, generating: bool) -> None:
        self.send_btn.setVisible(not generating)
        self.cancel_btn.setVisible(generating)
        self.input.setEnabled(not generating)

    def _clear_messages(self) -> None:
        while self.messages_layout.count() > 1:
            item = self.messages_layout.takeAt(0)
            if item is None:
                break
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _scroll_to_bottom(self) -> None:
        bar = self.scroll_area.verticalScrollBar()
        bar.setValue(bar.maximum())

    def _on_send(self) -> None:
        text = self.input.toPlainText().strip()
        if not text:
            return
        self.input.clear()
        self.send_message.emit(text)

    def _on_select(
        self, current: QListWidgetItem | None, _previous: QListWidgetItem | None
    ) -> None:
        if current is None:
            return
        conversation_id = int(current.data(Qt.ItemDataRole.UserRole))
        self.select_conversation.emit(conversation_id)

    def _on_delete(self) -> None:
        item = self.conversation_list.currentItem()
        if item is None:
            return
        conversation_id = int(item.data(Qt.ItemDataRole.UserRole))
        answer = QMessageBox.question(
            self,
            "Delete conversation",
            "Delete this conversation permanently?",
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.delete_conversation.emit(conversation_id)

    def _emit_flags(self) -> None:
        self.flags_changed.emit(self.use_docs.isChecked(), self.use_memory.isChecked())
