# Task Completion Checklist

After completing a coding task, run these checks:

1. **Lint**: `uv run ruff check` — fix any issues with `uv run ruff check --fix`
2. **Format**: `uv run ruff format` — ensure code is properly formatted
3. **Type check**: `uv run basedpyright --stats` — resolve any type errors
4. **Test**: `uv run pytest` — ensure all tests pass

Or run all at once: `make pre-commit`

## When adding a new resource command

- Create `src/kscli/commands/<resource>.py` with `register_<verb>()` functions
- Register the commands in `src/kscli/cli.py` on the appropriate verb groups
- Add tests in `tests/test_cli_<resource>.py` using `cli_helpers.run_kscli_ok`/`run_kscli_fail`
