# Development guide

## Prerequisites

- Python 3.13+
- Git
- Ollama (for manual end-to-end testing)

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"
```

## Run

```bash
local-ai
# or
python -m local_ai
```

## Quality gates

```bash
ruff check src tests
ruff format src tests
mypy src
pytest
```

## Project layout

| Path | Purpose |
|------|---------|
| `src/local_ai/app.py` | Qt bootstrap + main window |
| `src/local_ai/core/` | DB, migrations, settings, models |
| `src/local_ai/services/` | Business logic |
| `src/local_ai/workers/` | Background threads |
| `src/local_ai/ui/` | Views, themes, widgets |
| `tests/` | Automated tests |
| `packaging/` | Desktop packaging scripts |

## Adding a migration

1. Increment `CURRENT_SCHEMA_VERSION` in `core/migrations.py`
2. Append `(version, sql)` to `MIGRATIONS`
3. Add a test asserting the new version/tables

## Debugging

Logs rotate under the platform user log directory for `local-ai`.
Set logging to DEBUG in `logging_setup.setup_logging` when diagnosing issues.
