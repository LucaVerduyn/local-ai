"""Background Qt workers for non-blocking heavy work."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QObject, QThread, Signal, Slot

logger = logging.getLogger(__name__)


class WorkerThread(QThread):
    """Generic worker that runs a callable off the UI thread."""

    progress = Signal(str)
    finished_ok = Signal(object)
    failed = Signal(str)

    def __init__(
        self,
        fn: Callable[..., Any],
        *args: Any,
        parent: QObject | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(parent)
        self._fn = fn
        self._args = args
        self._kwargs = kwargs
        self._cancel = False

    def request_cancel(self) -> None:
        self._cancel = True

    def is_cancelled(self) -> bool:
        return self._cancel

    def emit_progress(self, message: str) -> None:
        self.progress.emit(message)

    @Slot()
    def run(self) -> None:
        try:
            result = self._fn(
                *self._args,
                progress=self.emit_progress,
                cancel_check=self.is_cancelled,
                **self._kwargs,
            )
            if self._cancel:
                self.failed.emit("Cancelled")
            else:
                self.finished_ok.emit(result)
        except Exception as exc:
            logger.exception("Worker failed")
            self.failed.emit(str(exc))


class ChatStreamWorker(QThread):
    """Stream chat tokens from ChatService without blocking the UI."""

    token = Signal(str)
    citations = Signal(object)
    finished_ok = Signal()
    failed = Signal(str)

    def __init__(
        self,
        stream_fn: Callable[..., Any],
        *,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._stream_fn = stream_fn
        self._cancel = False

    def request_cancel(self) -> None:
        self._cancel = True

    def is_cancelled(self) -> bool:
        return self._cancel

    @Slot()
    def run(self) -> None:
        try:
            for item in self._stream_fn(cancel_check=self.is_cancelled):
                if isinstance(item, list):
                    self.citations.emit(item)
                else:
                    self.token.emit(str(item))
                if self._cancel:
                    break
            self.finished_ok.emit()
        except Exception as exc:
            logger.exception("Chat stream worker failed")
            self.failed.emit(str(exc))
