# Build a Linux folder distribution (one-folder) with PyInstaller.
# Requires: Python 3.13+, PySide6 system deps (libEGL, xcb, etc.), Ollama separately.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

PYTHON="${ROOT}/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  PYTHON="python3"
fi

echo "Using Python: $PYTHON"
"$PYTHON" -m pip install -e ".[packaging]"
"$PYTHON" -m PyInstaller \
  --noconfirm \
  --clean \
  --distpath "$(dirname "$0")/dist" \
  --workpath "$(dirname "$0")/build" \
  "$(dirname "$0")/local_ai.spec"

echo "Done. Output: $(dirname "$0")/dist/LocalAI/"
