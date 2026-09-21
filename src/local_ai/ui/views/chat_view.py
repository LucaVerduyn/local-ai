"""Chat view with streaming, cancellation, and conversation history."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from local_ai.core.models import Conversation, Message
from local_ai.ui.widgets import ComposerEdit, EmptyState, MessageBubble, StreamingBubble


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
        self._generating = False

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        root.addWidget(splitter)

        side = QWidget()
        side.setObjectName("ChatSidebar")
        side_layout = QVBoxLayout(side)
        side_layout.setContentsMargins(16, 18, 12, 16)
        side_layout.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel("Chats")
        title.setObjectName("ChatSidebarTitle")
        new_btn = QPushButton("New chat")
        new_btn.setProperty("class", "Primary")
        new_btn.setToolTip("Start a new conversation")
        new_btn.clicked.connect(self.new_chat.emit)
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(new_btn)
        side_layout.addLayout(header)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search chats…")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.search_changed.emit)
        side_layout.addWidget(self.search)

        self.conversation_list = QListWidget()
        self.conversation_list.setObjectName("ConversationList")
        self.conversation_list.setSpacing(2)
        self.conversation_list.currentItemChanged.connect(self._on_select)
        side_layout.addWidget(self.conversation_list, 1)

        delete_btn = QPushButton("Delete")
        delete_btn.setProperty("class", "Danger")
        delete_btn.setToolTip("Delete the selected conversation")
        delete_btn.clicked.connect(self._on_delete)
        side_layout.addWidget(delete_btn)
        splitter.addWidget(side)

        main = QWidget()
        main_layout = QVBoxLayout(main)
        main_layout.setContentsMargins(20, 18, 24, 16)
        main_layout.setSpacing(12)

        top = QHBoxLayout()
        self.chat_title = QLabel("Chat")
        self.chat_title.setObjectName("ChatTitle")
        self.status_chip = QLabel("")
        self.status_chip.setObjectName("StatusChip")
        self.status_chip.setVisible(False)
        self.use_docs = QCheckBox("Documents")
        self.use_docs.setChecked(True)
        self.use_docs.setToolTip("Ground answers in your imported documents")
        self.use_memory = QCheckBox("Memory")
        self.use_memory.setChecked(True)
        self.use_memory.setToolTip("Use your saved local memory notes")
        self.use_docs.stateChanged.connect(self._emit_flags)
        self.use_memory.stateChanged.connect(self._emit_flags)
        top.addWidget(self.chat_title, 1)
        top.addWidget(self.status_chip)
        top.addWidget(self.use_docs)
        top.addWidget(self.use_memory)
        main_layout.addLayout(top)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setObjectName("ChatScroll")
        self.messages_host = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_host)
        self.messages_layout.setContentsMargins(4, 4, 4, 4)
        self.messages_layout.setSpacing(14)
        self.messages_layout.addStretch(1)
        self.scroll_area.setWidget(self.messages_host)
        main_layout.addWidget(self.scroll_area, 1)

        self.empty = EmptyState(
            "Start a conversation",
            "Ask anything. Press Enter to send, Shift+Enter for a new line. "
            "Answers stay on this device.",
        )
        main_layout.addWidget(self.empty)

        composer_frame = QFrame()
        composer_frame.setObjectName("ComposerFrame")
        composer = QVBoxLayout(composer_frame)
        composer.setContentsMargins(12, 10, 12, 10)
        composer.setSpacing(8)

        self.input = ComposerEdit()
        self.input.setPlaceholderText("Message Local AI…  (Enter to send)")
        self.input.setFixedHeight(92)
        self.input.setTabChangesFocus(True)
        self.input.submit_requested.connect(self._on_send)
        composer.addWidget(self.input)

        actions = QHBoxLayout()
        hint = QLabel("Enter to send · Shift+Enter for newline")
        hint.setProperty("class", "Muted")
        self.send_btn = QPushButton("Send")
        self.send_btn.setProperty("class", "Primary")
        self.send_btn.setMinimumWidth(96)
        self.send_btn.setDefault(True)
        self.send_btn.clicked.connect(self._on_send)
        self.cancel_btn = QPushButton("Stop")
        self.cancel_btn.setProperty("class", "Danger")
        self.cancel_btn.setMinimumWidth(96)
        self.cancel_btn.setVisible(False)
        self.cancel_btn.clicked.connect(self.cancel_generation.emit)
        actions.addWidget(hint, 1)
        actions.addWidget(self.send_btn)
        actions.addWidget(self.cancel_btn)
        composer.addLayout(actions)
        main_layout.addWidget(composer_frame)

        splitter.addWidget(main)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([300, 780])

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

    def show_conversation(
        self,
        conversation: Conversation | None,
        messages: list[Message],
        *,
        keep_generating: bool | None = None,
    ) -> None:
        self._clear_messages()
        self._streaming = None
        if keep_generating is None:
            keep_generating = self._generating
        if conversation is None:
            self._current_id = None
            self.chat_title.setText("Chat")
            self.empty.setVisible(True)
            self.scroll_area.setVisible(False)
            self.set_generating(False)
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
        self.set_generating(keep_generating)
        self._scroll_to_bottom()

    def begin_streaming(self) -> None:
        self._streaming = StreamingBubble()
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, self._streaming)
        self.set_generating(True)
        self.set_status_chip("Generating…")
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
        self.set_status_chip("")
        self._streaming = None

    def set_generating(self, generating: bool) -> None:
        self._generating = generating
        self.send_btn.setVisible(not generating)
        self.send_btn.setEnabled(not generating)
        self.cancel_btn.setVisible(generating)
        self.input.setEnabled(not generating)
        if not generating:
            self.input.setFocus()

    def set_status_chip(self, text: str) -> None:
        self.status_chip.setText(text)
        self.status_chip.setVisible(bool(text))

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
        if self._generating:
            return
        text = self.input.toPlainText().strip()
        if not text:
            return
        self.input.clear()
        self.send_message.emit(text)

    def _on_select(
        self, current: QListWidgetItem | None, _previous: QListWidgetItem | None
    ) -> None:
        if current is None or self._generating:
            return
        conversation_id = int(current.data(Qt.ItemDataRole.UserRole))
        if conversation_id == self._current_id:
            return
        self.select_conversation.emit(conversation_id)

    def _on_delete(self) -> None:
        if self._generating:
            return
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
