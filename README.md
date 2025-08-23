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

## Codex Memory Add

You can append new memories to `CODEX.md` using the `mem:add` command:

```bash
codex mem:add <Section> --id <id> --tags <tag1,tag2> --text "content" [--scope project|global|module]
```

The command acquires a lock while writing, redacts obvious secrets, and prints a
unified diff of the changes before committing them.

## Codex Memory Update

Existing memories can be modified with the `mem:update` command:

```bash
codex mem:update <id> --text "new content" [--tags tag1,tag2] [--scope project|global|module]
```

The command shows a unified diff of the changes and requires confirmation before
overwriting the entry. The text is redacted for obvious secrets, and an
`updated` timestamp is recorded.

## Codex Memory Delete

Entries can be archived using the `mem:delete` command which marks the entry with
`ttl: "0d"`:

```bash
codex mem:delete <id> [--scope project|global|module] [--yes]
```

Without `--yes` the command will prompt for confirmation before writing the
change.

## Codex Memory Compact

Expired entries and excess snippets can be removed with `mem:compact`:

```bash
codex mem:compact [--scope project|global|module] [--max-snippets N]
```

Entries with `ttl: "0d"` are purged and the file is trimmed to at most
`N` snippets.

## Codex Memory Lint

The `mem:lint` command validates `CODEX.md` for structural issues:

```bash
codex mem:lint [--scope project|global|module]
```

It reports malformed YAML, duplicate ids, missing sections, and files exceeding
200 lines.

## Task Commands

The CLI can track active tasks and record progress notes:

```bash
codex mem:task bind TASKID
codex mem:task checkpoint "did something"
codex mem:task next "bullet one;bullet two"
codex mem:task sync
codex mem:task complete
```

Binding creates a journal under `.codex/tasks/` and a matching entry in
`CODEX.md`. Notes and next steps are appended to the journal, `sync` updates the
memory entry, and `complete` archives the task.

## Cross-Repo and Code Commands

Additional helpers operate on code across the workspace:

- `codex xrepo:search <regex> --repos repo1,repo2` runs ripgrep across multiple repositories.
- `codex code:edges refresh` rebuilds an `EDGES.md` file from markdown links.
- `codex code:symbols refresh` regenerates `SYMBOLS.md` using ctags output.
- `codex code:hotset add <path> --reason "why"` tracks important files in `HOTSET.md`.
- `codex code:snip <path[:L1-L2]>` saves a snippet into `SNIPPETS/`.
- `codex code:compact` prunes snippets older than 30 days.

## MCP Methods

The `codex.mcp` module provides programmatic access to the same features as the
CLI. These functions operate on the project workspace and can be used from
Python code:

```python
from codex import mcp
entries = mcp.mem_search({"q": "hello"})
mcp.mem_add({"section": "Project Facts", "entry": {"id": "a1", "text": "Hi"}})
mcp.mem_update({"id": "a1", "patch": {"text": "Updated"}})
mcp.mem_delete({"id": "a1", "confirm": True})
mcp.mem_task_bind({"id": "T1"})
mcp.mem_task_checkpoint({"note": "did something", "next": ["next step"]})
mcp.code_edges_refresh()
mcp.code_symbols_refresh()
mcp.code_snip({"path": "file.py", "start": 1, "end": 5})
```

The functions return Python data structures or file paths, enabling integration
with other tooling or editors.
