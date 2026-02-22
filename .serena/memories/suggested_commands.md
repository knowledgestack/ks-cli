# Suggested Commands

## Development Setup
```bash
uv sync --all-extras --group dev     # Install all dependencies
uv run pre-commit install            # Install pre-commit hooks
```

## Linting & Formatting
```bash
uv run ruff check                    # Lint
uv run ruff check --fix              # Lint + autofix
uv run ruff format                   # Format code
```

## Type Checking
```bash
uv run basedpyright --stats          # Type check
```

## Testing
```bash
uv run pytest                        # Run all tests
uv run pytest tests/test_cli_folders.py  # Single test file
uv run pytest tests/test_cli_folders.py::TestCliFolders::test_get_folders_root  # Single test
uv run pytest -x                     # Stop on first failure
```

## Pre-commit (all checks)
```bash
make pre-commit                      # Runs lint + typecheck + test
```

## Running the CLI
```bash
uv run kscli --help                  # Show CLI help
uv run python -m kscli              # Alternative entry point
```

## System utilities (macOS/Darwin)
```bash
git status / git diff / git log      # Git operations
ls / find / grep                     # File operations (standard unix)
```
