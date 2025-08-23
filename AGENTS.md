# Repository Guidelines

## Project Structure & Module Organization
- `codex/cli.py`: Click-based CLI commands (`mem:*`). Keep I/O and UX here.
- `codex/memory.py`: Parsing, search, scoring, and redaction logic. Keep pure and testable.
- `tests/`: Pytest tests using `click.testing.CliRunner` and `isolated_filesystem`.
- `.codex/CODEX.md`: Project-scoped memory file created/edited by commands.

## Build, Test, and Development Commands
- Install (editable): `pip install -e .` (requires Python 3.9+).
- Run CLI during dev: `python -m codex.cli mem:search "query" --scope project`.
  - If installed with an entrypoint, you can run: `codex mem:search ...`.
- Run tests: `pytest -q` or `python -m pytest -q`.
- Lint `CODEX.md`: `python -m codex.cli mem:lint --scope project`.
- Compact memories: `python -m codex.cli mem:compact --max-snippets 100`.

## Coding Style & Naming Conventions
- Python, 4-space indentation, PEP 8. Prefer type hints and f-strings.
- Modules/files: `lower_snake_case.py`; functions/variables: `lower_snake_case`; classes: `PascalCase`.
- Keep CLI side-effectful code in `cli.py`; keep logic in `memory.py` for reuse.
- Avoid leaking secrets in logs/output—use `redact()` for any free text.

## Testing Guidelines
- Framework: `pytest`. Place tests under `tests/` named `test_*.py`.
- Use `CliRunner` with `isolated_filesystem()` for CLI tests; write temp `CODEX.md` fixtures under `.codex/`.
- Add tests for new commands, flags, or parsing rules. Keep outputs deterministic (e.g., confirm diffs where applicable).

## Commit & Pull Request Guidelines
- Messages: concise, imperative; use scopes when helpful, e.g., `feat(cli): add compact`, `fix(memory): handle empty section`.
- PRs should include: clear summary, linked issue (if any), before/after examples (diff or command output), and updated tests/README when behavior changes.
- Keep PRs focused and small. Touch `cli.py` for UX, `memory.py` for logic, and add/adjust tests accordingly.

## Security & Configuration Tips
- Memory files may contain sensitive text. The CLI redacts obvious emails/tokens; still avoid pasting secrets.
- Project scope uses `.codex/CODEX.md`; global scope uses `~/.codex/memory/CODEX.md`.
