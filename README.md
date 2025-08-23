# MemoryManagerForCodex

Memory Manager for OpenAI Codex CLI.

## Codex Memory Search

The project ships a `codex` command line tool that can search project or global
memories stored in `CODEX.md` files.

### Usage

```bash
codex mem:search "query" [--scope project|global|module] [--k N]
```

- `--scope` selects which `CODEX.md` to search:
  - `project` (default) looks for `.codex/CODEX.md` in the current directory.
  - `global` searches `~/.codex/memory/CODEX.md`.
  - `module` may be used for future module-specific memories.
- `--k` limits the number of results returned (default 5).

If no `CODEX.md` exists for the selected scope, the command prints a helpful
message instead of failing.
