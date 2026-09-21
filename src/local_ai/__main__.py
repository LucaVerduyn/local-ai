"""Application entry point."""

from __future__ import annotations

import sys


def main() -> int:
    """Launch the Local AI desktop application."""
    from local_ai.app import run

    return run(sys.argv)


if __name__ == "__main__":
    raise SystemExit(main())
