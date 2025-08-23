# Development Tasks

This file outlines implementation tasks for the Codex CLI and MCP, derived from `codex_local_memory_design_full.md`.

## CLI - Memory Commands
- [x] **Search**: Implement `codex mem:search <query> [--scope <scope>] [--k <k>]` to query CODEX.md files.
  - [x] Build in-memory index from CODEX.md with weights and recency.
  - [x] **Tests**: Ensure search returns expected entries by section, honors scope/k limits, and handles missing files gracefully.
- [x] **Add**: Implement `codex mem:add <Section> --id <id> --tags <tags> --text <text>`.
  - [x] Write to CODEX.md with dry-run diff, lock file, and secret redaction.
  - [x] **Tests**: Verify diff output, lock enforcement on concurrent writes, redaction, and successful append.
- [x] **Update**: Implement `codex mem:update <id> --text <text> [--tags <tags>]`.
  - [x] Apply in-place edit via patch with confirmation.
  - [x] **Tests**: Confirm fields are updated correctly and diff is shown before write.
- [x] **Delete**: Implement `codex mem:delete <id> [--yes]`.
   - [x] Mark entry archived with `ttl: "0d"` or remove on confirmation.
   - [x] **Tests**: Verify deletion behavior with and without `--yes` flag.
- [x] **Compact**: Implement `codex mem:compact` to remove expired entries and enforce max_snippets.
   - [x] **Tests**: Ensure TTL entries are removed and file stays under size limits.
- [x] **Lint**: Implement `codex mem:lint` to catch malformed YAML, duplicate ids, missing sections, or overlong files.
   - [x] **Tests**: Cover malformed front matter, duplicate ids, and over‑200‑line files.

## CLI - Task Commands
- [x] **Bind**: Implement `codex mem:task bind <ID>` to set active task and create journal file.
  - [x] **Tests**: Verify binding creates `.codex/tasks/<ID>.md` and updates CODEX shard.
- [x] **Checkpoint**: Implement `codex mem:task checkpoint "<note>"`.
  - [x] **Tests**: Append note to task journal with timestamp.
- [x] **Next**: Implement `codex mem:task next "<bullets>"` to record next steps.
  - [x] **Tests**: Ensure bullets are written and preserved across sessions.
- [x] **Sync**: Implement `codex mem:task sync` to reconcile task shard in CODEX.md with journal.
  - [x] **Tests**: Detect drift and update accordingly.
- [x] **Complete**: Implement `codex mem:task complete` to mark task done and archive journal.
  - [x] **Tests**: Journal is archived and task status updated.

## CLI - Cross-Repo / Code Commands
- [x] **Search**: Implement `codex xrepo:search <regex> [--repos list]` using ripgrep across workspace repos.
  - [x] **Tests**: Stub ripgrep calls and confirm correct repo set.
- [x] **Edges Refresh**: Implement `codex code:edges refresh` to rebuild `EDGES.md` digest.
  - [x] **Tests**: Ensure file generated and contains expected links.
- [x] **Symbols Refresh**: Implement `codex code:symbols refresh` to regenerate `SYMBOLS.md` via ctags.
  - [x] **Tests**: Verify symbols are parsed and stored.
- [x] **Hotset Add**: Implement `codex code:hotset add <path> [--reason <...>]` to mark important files.
  - [x] **Tests**: File is appended with reason and deduplicated.
- [x] **Snip**: Implement `codex code:snip <path[:L1-L2]>` to capture code snippets into `SNIPPETS/`.
  - [x] **Tests**: Snippet saved with correct line numbers and reference.
- [x] **Compact**: Implement `codex code:compact` to prune old digests/snippets.
  - [x] **Tests**: Old digests are removed and metrics logged.

## MCP Methods
- [x] **mem.search**: Expose search as `mem.search({q, scope?, k?})`.
  - [x] **Tests**: Unit tests for correct result format and scope handling.
- [x] **mem.add**: Expose add as `mem.add({scope, section, entry})`.
  - [x] **Tests**: Ensure returned id matches stored entry and redaction occurs.
- [x] **mem.update**: Expose update as `mem.update({scope, id, patch})`.
  - [x] **Tests**: Verify fields patched and diff confirmed.
- [x] **mem.delete**: Expose delete as `mem.delete({scope, id, confirm})`.
  - [x] **Tests**: Confirm deletion requires confirmation and archives entry.
- [x] **mem.task.bind**: Implement task binding via MCP.
  - [x] **Tests**: Journal created and active task recorded.
- [x] **mem.task.checkpoint**: Implement checkpoint with optional next steps.
  - [x] **Tests**: Note and next steps appended with timestamps.
- [x] **code.edges.refresh**: MCP method returning path to `EDGES.md`.
  - [x] **Tests**: Trigger digest rebuild and return correct path.
- [x] **code.symbols.refresh**: MCP method for `SYMBOLS.md`.
  - [x] **Tests**: Confirm symbols file generated.
- [x] **code.snip**: MCP method to extract snippet.
  - [x] **Tests**: Validate snippet path and content range.

## Shared Utilities & Testing
- [x] Implement CODEX.md parser and writer per schema.
  - [x] **Tests**: Malformed YAML, duplicate ids, TTL handling, performance (≤5ms on 200 lines).
- [x] Implement redaction filter for emails, API keys, tokens.
  - [x] **Tests**: Ensure sensitive strings are removed before write.
- [x] Setup continuous integration with `pytest` running all test suites.

