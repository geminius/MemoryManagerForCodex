# Repository Guidelines

## Project Structure & Module Organization
- `codex/cli.py`: Click-based CLI commands (`mem:*`). Keep I/O and UX here.
- `codex/memory.py`: Parsing, search, scoring, and redaction logic. Keep pure and testable.
- `tests/`: Pytest tests using `click.testing.CliRunner` and `isolated_filesystem`.
- `.codex/CODEX.md`: Project-scoped memory file created/edited by commands.
- `codex_local_memory_design_full.md`: Design doc; some MCP ideas here are not yet implemented.

## Build, Test, and Development Commands
- Install (editable): `pip install -e .` (Python 3.9+).
- Run CLI: `codex mem:search "query" --scope project` (console script).
  - Alt: `python -m codex.cli mem:search "query"`.
- Run tests: `pytest -q` or `python -m pytest -q`.
- Lint `CODEX.md`: `codex mem:lint --scope project`.
- Compact memories: `codex mem:compact --max-snippets 100`.

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

## Agent & MCP Instructions
- Non-interactive usage (agents):
  - Add: `codex mem:add "Guardrails" --id guard-1 --tags safety --text "Never run destructive migrations."`
  - Update (no prompt): `codex mem:update guard-1 --text "Never drop prod tables." --tags safety,db --yes`.
  - Delete (no prompt): `codex mem:delete guard-1 --yes`.
- MCP status: No native MCP server in this repo. If your host can expose shell tools, map MCP methods to CLI commands (e.g., `mem.search` → `codex mem:search`). The design doc outlines future MCP endpoints.

## Security & Configuration Tips
- Memory files may contain sensitive text. The CLI redacts obvious emails/tokens; still avoid pasting secrets.
- Scopes: project `.codex/CODEX.md`; global `~/.codex/memory/CODEX.md`. Keep permissions restrictive.
