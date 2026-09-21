# Build a macOS .app bundle with PyInstaller.
# Requires: Python 3.13+, Xcode CLT recommended, Ollama separately.
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

echo "Done. Output: $(dirname "$0")/dist/LocalAI.app"
