# Contributing to Local AI

Thanks for helping improve Local AI.

## Development setup

1. Install Python 3.13+
2. Install and start [Ollama](https://ollama.com) for manual testing
3. Clone the repository and create a virtual environment
4. Install editable dependencies:

```bash
pip install -e ".[dev]"
```

## Workflow

1. Create a branch from `main`
2. Make focused changes with clear commits
3. Run quality checks:

```bash
ruff check src tests
ruff format --check src tests
mypy src
pytest
```

4. Open a pull request using the template

## Guidelines

- Keep the app fully local — no cloud backends or telemetry
- Prefer small, reviewable pull requests
- Add tests for new behavior
- Use type hints on public functions
- Do not commit user data, databases, or model weights

## Code style

- Ruff for linting and formatting
- mypy in strict mode for `src/local_ai`
- Prefer clear names over clever abstractions

## Reporting issues

Use GitHub Issues. Include OS, Python version, Ollama version, and steps to reproduce.
