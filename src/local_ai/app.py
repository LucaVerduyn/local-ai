"""Application bootstrap and main window."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from local_ai import __app_name__, __version__
from local_ai.config import ORG_NAME, SUPPORTED_DOCUMENT_EXTENSIONS, database_path
from local_ai.core.database import Database
from local_ai.core.models import ThemeMode
from local_ai.core.settings import SettingsStore
from local_ai.logging_setup import setup_logging
from local_ai.services.chat_service import ChatService
from local_ai.services.document_service import DocumentService
from local_ai.services.embedding_service import EmbeddingService
from local_ai.services.memory_service import MemoryService
from local_ai.services.ollama_client import OllamaClient
from local_ai.services.rag_service import RAGService
from local_ai.ui.themes import apply_theme
from local_ai.ui.views.chat_view import ChatView
from local_ai.ui.views.documents_view import DocumentsView
from local_ai.ui.views.home_view import HomeView
from local_ai.ui.views.memory_view import MemoryView
from local_ai.ui.views.models_view import ModelsView
from local_ai.ui.views.settings_view import SettingsView
from local_ai.workers import ChatStreamWorker, WorkerThread

logger = logging.getLogger(__name__)


def run(argv: list[str] | None = None) -> int:
    """Create the Qt application and show the main window."""
    setup_logging()
    args = argv if argv is not None else sys.argv
    app = QApplication(args)
    app.setApplicationName(__app_name__)
    app.setOrganizationName(ORG_NAME)
    app.setApplicationVersion(__version__)
    app.setStyle("Fusion")

    settings = SettingsStore()
    apply_theme(app, settings.settings.theme)

    db = Database(database_path())
    db.migrate()

    window = MainWindow(db=db, settings=settings)
    window.show()
    logger.info("Local AI started (v%s)", __version__)
    return app.exec()


NAV_ITEMS = [
    ("home", "Home"),
    ("chat", "Chat"),
    ("documents", "Documents"),
    ("memory", "Memory"),
    ("models", "Models"),
    ("settings", "Settings"),
]


class MainWindow(QMainWindow):
    def __init__(
        self,
        *,
        db: Database,
        settings: SettingsStore,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.db = db
        self.settings_store = settings
        self.setWindowTitle(f"{__app_name__}")
        self.resize(1180, 760)
        self.setMinimumSize(900, 600)

        self._workers: list[WorkerThread | ChatStreamWorker] = []
        self._chat_worker: ChatStreamWorker | None = None
        self._current_conversation_id: int | None = None

        self._rebuild_services()
        self._build_ui()
        self._connect_signals()
        self._apply_current_theme()
        self._refresh_home_status()
        self.refresh_conversations()
        self.refresh_documents()
        self.refresh_memory()
        self.refresh_models()
        self.settings_view.load_settings(self.settings_store.settings)

        QTimer.singleShot(400, self._refresh_home_status)

    def _rebuild_services(self) -> None:
        cfg = self.settings_store.settings
        self.ollama = OllamaClient(cfg.ollama_base_url)
        self.embedding = EmbeddingService(self.ollama, cfg.embedding_model)
        self.documents = DocumentService(
            self.db,
            self.embedding,
            chunk_size=cfg.chunk_size,
            chunk_overlap=cfg.chunk_overlap,
        )
        self.rag = RAGService(self.db, self.embedding)
        self.memory = MemoryService(self.db, self.embedding)
        self.chat = ChatService(self.db, self.settings_store, self.ollama, self.rag, self.memory)

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        sidebar = QWidget()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(210)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(14, 18, 14, 18)
        side_layout.setSpacing(6)

        brand = QLabel(__app_name__)
        brand.setObjectName("BrandLabel")
        sub = QLabel("Private · Local · Yours")
        sub.setObjectName("BrandSub")
        side_layout.addWidget(brand)
        side_layout.addWidget(sub)

        self.nav_buttons: dict[str, QPushButton] = {}
        for key, label in NAV_ITEMS:
            button = QPushButton(label)
            button.setProperty("class", "NavButton")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda _checked=False, k=key: self.navigate(k))
            side_layout.addWidget(button)
            self.nav_buttons[key] = button
        side_layout.addStretch(1)

        version = QLabel(f"v{__version__}")
        version.setProperty("class", "Muted")
        side_layout.addWidget(version)
        layout.addWidget(sidebar)

        self.stack = QStackedWidget()
        self.home_view = HomeView()
        self.chat_view = ChatView()
        self.documents_view = DocumentsView()
        self.memory_view = MemoryView()
        self.models_view = ModelsView()
        self.settings_view = SettingsView()

        self._pages = {
            "home": self.home_view,
            "chat": self.chat_view,
            "documents": self.documents_view,
            "memory": self.memory_view,
            "models": self.models_view,
            "settings": self.settings_view,
        }
        for widget in self._pages.values():
            self.stack.addWidget(widget)
        layout.addWidget(self.stack, 1)

        status = QStatusBar()
        self.setStatusBar(status)
        self.status_label = QLabel("Ready")
        status.addWidget(self.status_label)

        quit_action = QAction("Quit", self)
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        quit_action.triggered.connect(self.close)
        self.addAction(quit_action)

        self.navigate("home")

    def _connect_signals(self) -> None:
        self.home_view.open_chat.connect(lambda: self.navigate("chat"))
        self.home_view.open_documents.connect(lambda: self.navigate("documents"))
        self.home_view.open_models.connect(lambda: self.navigate("models"))
        self.home_view.open_settings.connect(lambda: self.navigate("settings"))

        self.chat_view.new_chat.connect(self.create_conversation)
        self.chat_view.select_conversation.connect(self.open_conversation)
        self.chat_view.delete_conversation.connect(self.delete_conversation)
        self.chat_view.send_message.connect(self.send_chat_message)
        self.chat_view.cancel_generation.connect(self.cancel_chat)
        self.chat_view.search_changed.connect(self.refresh_conversations)
        self.chat_view.flags_changed.connect(self.update_conversation_flags)

        self.documents_view.import_requested.connect(self.import_documents)
        self.documents_view.reindex_requested.connect(self.reindex_document)
        self.documents_view.delete_requested.connect(self.delete_document)
        self.documents_view.search_changed.connect(self.refresh_documents)
        self.documents_view.list.currentItemChanged.connect(
            lambda current, _prev: self._show_selected_document(current)
        )

        self.memory_view.add_requested.connect(self.add_memory)
        self.memory_view.delete_requested.connect(self.delete_memory)
        self.memory_view.search_changed.connect(self.refresh_memory)

        self.models_view.refresh_requested.connect(self.refresh_models)
        self.models_view.pull_requested.connect(self.pull_model)
        self.models_view.delete_requested.connect(self.delete_model)
        self.models_view.set_chat_model.connect(self.set_chat_model)
        self.models_view.set_embedding_model.connect(self.set_embedding_model)

        self.settings_view.save_requested.connect(self.save_settings)
        self.settings_view.reset_requested.connect(
            lambda: self.settings_view.load_settings(self.settings_store.settings)
        )

    def navigate(self, key: str) -> None:
        widget = self._pages[key]
        self.stack.setCurrentWidget(widget)
        for nav_key, button in self.nav_buttons.items():
            button.setProperty("active", "true" if nav_key == key else "false")
            button.style().unpolish(button)
            button.style().polish(button)
        if key == "chat":
            self.refresh_conversations()
        elif key == "documents":
            self.refresh_documents()
        elif key == "memory":
            self.refresh_memory()
        elif key == "models":
            self.refresh_models()
        elif key == "home":
            self._refresh_home_status()

    def _apply_current_theme(self) -> None:
        application = QApplication.instance()
        if isinstance(application, QApplication):
            apply_theme(application, self.settings_store.settings.theme)

    def set_status(self, message: str) -> None:
        self.status_label.setText(message)

    def _track_worker(self, worker: WorkerThread | ChatStreamWorker) -> None:
        self._workers.append(worker)

        def _cleanup() -> None:
            if worker in self._workers:
                self._workers.remove(worker)
            worker.deleteLater()

        worker.finished.connect(_cleanup)

    # --- Home ---
    def _refresh_home_status(self) -> None:
        available = self.ollama.is_available()
        docs = len(self.documents.list_documents())
        chats = len(self.chat.list_conversations())
        if available:
            self.home_view.set_status(
                "Ollama is online",
                f"{chats} conversation(s) · {docs} document(s). You're ready to chat privately.",
            )
        else:
            cfg = self.settings_store.settings
            self.home_view.set_status(
                "Ollama is offline",
                f"Start Ollama and ensure it is reachable at {cfg.ollama_base_url}. "
                "Then pull a chat model and an embedding model.",
            )

    # --- Chat ---
    def refresh_conversations(self, query: str = "") -> None:
        conversations = self.chat.list_conversations(query=query or None)
        self.chat_view.set_conversations(conversations, self._current_conversation_id)
        if self._current_conversation_id is not None:
            conversation = self.chat.get_conversation(self._current_conversation_id)
            if conversation:
                messages = self.chat.get_messages(conversation.id)
                self.chat_view.show_conversation(conversation, messages)
            else:
                self._current_conversation_id = None
                self.chat_view.show_conversation(None, [])

    def create_conversation(self) -> None:
        cfg = self.settings_store.settings
        conversation = self.chat.create_conversation(model=cfg.chat_model)
        self._current_conversation_id = conversation.id
        self.refresh_conversations()
        self.navigate("chat")
        self.set_status(f"Started conversation #{conversation.id}")

    def open_conversation(self, conversation_id: int) -> None:
        self._current_conversation_id = conversation_id
        conversation = self.chat.get_conversation(conversation_id)
        if conversation is None:
            return
        messages = self.chat.get_messages(conversation_id)
        self.chat_view.show_conversation(conversation, messages)

    def delete_conversation(self, conversation_id: int) -> None:
        self.chat.delete_conversation(conversation_id)
        if self._current_conversation_id == conversation_id:
            self._current_conversation_id = None
            self.chat_view.show_conversation(None, [])
        self.refresh_conversations()

    def update_conversation_flags(self, use_documents: bool, use_memory: bool) -> None:
        if self._current_conversation_id is None:
            return
        self.chat.set_flags(
            self._current_conversation_id,
            use_documents=use_documents,
            use_memory=use_memory,
        )

    def send_chat_message(self, text: str) -> None:
        if self._chat_worker is not None and self._chat_worker.isRunning():
            return
        if self._current_conversation_id is None:
            self.create_conversation()
        assert self._current_conversation_id is not None

        try:
            self.chat.add_user_message(self._current_conversation_id, text)
        except ValueError as exc:
            QMessageBox.warning(self, "Chat", str(exc))
            return

        conversation = self.chat.get_conversation(self._current_conversation_id)
        messages = self.chat.get_messages(self._current_conversation_id)
        if conversation:
            self.chat_view.show_conversation(conversation, messages)
        self.chat_view.begin_streaming()
        self.set_status("Generating…")

        conversation_id = self._current_conversation_id

        def stream_fn(*, cancel_check: object) -> object:
            return self.chat.stream_assistant_reply(
                conversation_id,
                cancel_check=cancel_check,  # type: ignore[arg-type]
            )

        worker = ChatStreamWorker(stream_fn)
        self._chat_worker = worker
        self._track_worker(worker)
        worker.token.connect(self.chat_view.append_token)
        worker.failed.connect(self._on_chat_failed)
        worker.finished_ok.connect(self._on_chat_finished)
        worker.start()

    def cancel_chat(self) -> None:
        if self._chat_worker is not None:
            self._chat_worker.request_cancel()
            self.set_status("Cancelling…")

    def _on_chat_failed(self, message: str) -> None:
        self.chat_view.end_streaming()
        self.set_status("Generation failed")
        QMessageBox.critical(self, "Chat error", message)
        self.refresh_conversations()

    def _on_chat_finished(self) -> None:
        self.chat_view.end_streaming()
        self.set_status("Ready")
        self.refresh_conversations()

    # --- Documents ---
    def refresh_documents(self, query: str = "") -> None:
        documents = self.documents.list_documents(query=query or None)
        self.documents_view.set_documents(documents)

    def _show_selected_document(self, current: object) -> None:
        if current is None:
            self.documents_view.show_document(None)
            return
        document_id = int(current.data(Qt.ItemDataRole.UserRole))  # type: ignore[attr-defined]
        self.documents_view.show_document(self.documents.get_document(document_id))

    def import_documents(self) -> None:
        extensions = " ".join(f"*{ext}" for ext in sorted(SUPPORTED_DOCUMENT_EXTENSIONS))
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Import documents",
            "",
            f"Documents ({extensions});;All files (*.*)",
        )
        if not paths:
            return
        for path_str in paths:
            try:
                document = self.documents.import_document(Path(path_str))
                self._start_index_worker(document.id)
            except Exception as exc:
                QMessageBox.warning(self, "Import failed", f"{path_str}\n{exc}")
        self.refresh_documents()

    def reindex_document(self, document_id: int) -> None:
        self._start_index_worker(document_id)

    def _start_index_worker(self, document_id: int) -> None:
        self.documents_view.set_busy(True, "Indexing…")
        self.set_status(f"Indexing document #{document_id}…")

        def work(*, progress: object, cancel_check: object) -> object:
            return self.documents.index_document(
                document_id,
                progress=progress,  # type: ignore[arg-type]
                cancel_check=cancel_check,  # type: ignore[arg-type]
            )

        worker = WorkerThread(work)
        self._track_worker(worker)
        worker.progress.connect(lambda msg: self.documents_view.set_busy(True, msg))
        worker.failed.connect(self._on_index_failed)
        worker.finished_ok.connect(self._on_index_finished)
        worker.start()

    def _on_index_failed(self, message: str) -> None:
        self.documents_view.set_busy(False)
        self.set_status("Indexing failed")
        QMessageBox.warning(self, "Indexing failed", message)
        self.refresh_documents()

    def _on_index_finished(self, _result: object) -> None:
        self.documents_view.set_busy(False)
        self.set_status("Document indexed")
        self.refresh_documents()

    def delete_document(self, document_id: int) -> None:
        self.documents.delete_document(document_id)
        self.refresh_documents()
        self.documents_view.show_document(None)

    # --- Memory ---
    def refresh_memory(self, query: str = "") -> None:
        items = self.memory.list_items(query=query or None)
        self.memory_view.set_items(items)

    def add_memory(self, content: str, tags: str, importance: int) -> None:
        def work(*, progress: object, cancel_check: object) -> object:
            _ = progress, cancel_check
            return self.memory.add(content, tags=tags, importance=importance)

        self.set_status("Saving memory…")
        worker = WorkerThread(work)
        self._track_worker(worker)
        worker.failed.connect(lambda msg: QMessageBox.warning(self, "Memory", msg))
        worker.finished_ok.connect(lambda _r: self._on_memory_saved())
        worker.start()

    def delete_memory(self, memory_id: int) -> None:
        self.memory.delete(memory_id)
        self.refresh_memory()

    def _on_memory_saved(self) -> None:
        self.refresh_memory()
        self.set_status("Memory saved")

    # --- Models ---
    def refresh_models(self) -> None:
        cfg = self.settings_store.settings
        available = self.ollama.is_available()
        if not available:
            self.models_view.set_connection_status(False, cfg.ollama_base_url)
            self.models_view.set_models([], cfg.chat_model, cfg.embedding_model)
            return
        try:
            models = self.ollama.list_models()
            self.models_view.set_connection_status(
                True, f"{len(models)} model(s) at {cfg.ollama_base_url}"
            )
            self.models_view.set_models(models, cfg.chat_model, cfg.embedding_model)
        except Exception as exc:
            self.models_view.set_connection_status(False, str(exc))
            self.models_view.set_models([], cfg.chat_model, cfg.embedding_model)

    def pull_model(self, name: str) -> None:
        self.models_view.set_progress(f"Pulling {name}…")
        self.set_status(f"Pulling model {name}…")

        def work(*, progress: object, cancel_check: object) -> object:
            _ = cancel_check

            def on_progress(message: str) -> None:
                progress(message)  # type: ignore[operator]

            self.ollama.pull_model(name, on_progress=on_progress)
            return name

        worker = WorkerThread(work)
        self._track_worker(worker)
        worker.progress.connect(self.models_view.set_progress)
        worker.failed.connect(self._on_pull_failed)
        worker.finished_ok.connect(self._on_pull_finished)
        worker.start()

    def _on_pull_failed(self, message: str) -> None:
        self.models_view.set_progress("")
        self.set_status("Pull failed")
        QMessageBox.critical(self, "Pull failed", message)

    def _on_pull_finished(self, name: object) -> None:
        self.models_view.set_progress(f"Pulled {name}")
        self.set_status("Model ready")
        self.refresh_models()

    def delete_model(self, name: str) -> None:
        try:
            self.ollama.delete_model(name)
            self.refresh_models()
            self.set_status(f"Deleted model {name}")
        except Exception as exc:
            QMessageBox.critical(self, "Delete failed", str(exc))

    def set_chat_model(self, name: str) -> None:
        self.settings_store.update(chat_model=name)
        self._rebuild_services()
        self.settings_view.load_settings(self.settings_store.settings)
        self.refresh_models()
        self.set_status(f"Chat model set to {name}")

    def set_embedding_model(self, name: str) -> None:
        self.settings_store.update(embedding_model=name)
        self._rebuild_services()
        self.settings_view.load_settings(self.settings_store.settings)
        self.refresh_models()
        self.set_status(f"Embedding model set to {name}")

    # --- Settings ---
    def save_settings(self, payload: dict[str, object]) -> None:
        try:
            theme = ThemeMode(str(payload["theme"]))
            self.settings_store.update(
                ollama_base_url=str(payload["ollama_base_url"]),
                chat_model=str(payload["chat_model"]),
                embedding_model=str(payload["embedding_model"]),
                temperature=float(str(payload["temperature"])),
                context_chunks=int(str(payload["context_chunks"])),
                chunk_size=int(str(payload["chunk_size"])),
                chunk_overlap=int(str(payload["chunk_overlap"])),
                memory_enabled=bool(payload["memory_enabled"]),
                theme=theme,
                system_prompt=str(payload["system_prompt"]),
            )
            self._rebuild_services()
            self._apply_current_theme()
            self.settings_view.load_settings(self.settings_store.settings)
            self._refresh_home_status()
            self.refresh_models()
            self.set_status("Settings saved")
            QMessageBox.information(self, "Settings", "Settings saved.")
        except Exception as exc:
            QMessageBox.critical(self, "Settings", f"Could not save settings:\n{exc}")

    def closeEvent(self, event: QCloseEvent) -> None:
        for worker in list(self._workers):
            if isinstance(worker, (ChatStreamWorker, WorkerThread)):
                worker.request_cancel()
            worker.wait(2000)
        self.db.close()
        super().closeEvent(event)
