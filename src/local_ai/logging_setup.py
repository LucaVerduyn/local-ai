"""Logging configuration for Local AI."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from local_ai.config import log_dir


def setup_logging(*, level: int = logging.INFO, log_file: Path | None = None) -> None:
    """Configure console and rotating file logging."""
    root = logging.getLogger()
    if root.handlers:
        return

    root.setLevel(level)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(formatter)
    root.addHandler(console)

    destination = log_file or (log_dir() / "local-ai.log")
    destination.parent.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        destination,
        maxBytes=2_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
