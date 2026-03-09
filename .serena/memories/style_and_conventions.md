# Style and Conventions

## Code Style

- **Line length**: 88 characters
- **Quote style**: Double quotes
- **Indent style**: Spaces
- **Docstrings**: Google convention (when present; most D1xx rules are ignored)
- **Type hints**: Used throughout; checked with basedpyright
- **Imports**: isort-managed, first-party packages: `shared_utils`, `database_schema`, `private_api_client`

## Ruff Rules

Extensive rule set enabled (E, W, F, I, UP, B, C4, DTZ, T10, G, PIE, PT, RET, SIM, TCH, ARG, PTH, ERA, PD, PGH, PL, RUF, D). Notable ignores:

- All missing docstring rules (D100-D107) are ignored
- E501 (line length) ignored — handled by formatter
- B008 (function call in default argument) ignored — common in Click/FastAPI
- Tests allow assert, unused args (fixtures), magic values

## Naming Conventions

- Command modules: `src/kscli/commands/<resource>.py`
- Test files: `tests/test_cli_<resource>.py`
- Registration functions: `register_<verb>(group: click.Group)`
- Column definitions: `COLUMNS = [...]` at module level

## Design Patterns

- **Verb-first routing**: Commands registered as `<verb> <resource>`, not `<resource> <verb>`
- **Registration pattern**: Each module exposes `register_<verb>()` functions, wired in `cli.py`
- **Error handling**: Always use `with handle_client_errors():` context manager around API calls
- **SDK usage**: `ksapi` is auto-generated — never modify it directly
- **Output**: Always pass through `to_dict()` → `print_result()` pipeline

## Commit Convention

Conventional commits (semantic-release): `feat:`, `fix:`, `perf:`, `chore:`, `ci:`, `docs:`, `style:`, `refactor:`, `test:`
