# Development Tasks

This file outlines implementation tasks for the Codex CLI and MCP, derived from `codex_local_memory_design_full.md`.

## CLI - Memory Commands
- [x] **Search**: Implement `codex mem:search <query> [--scope <scope>] [--k <k>]` to query CODEX.md files.
  - [x] Build in-memory index from CODEX.md with weights and recency.
  - [x] **Tests**: Ensure search returns expected entries by section, honors scope/k limits, and handles missing files gracefully.
- [ ] **Add**: Implement `codex mem:add <Section> --id <id> --tags <tags> --text <text>`.
  - [ ] Write to CODEX.md with dry-run diff, lock file, and secret redaction.
  - [ ] **Tests**: Verify diff output, lock enforcement on concurrent writes, redaction, and successful append.
- [ ] **Update**: Implement `codex mem:update <id> --text <text> [--tags <tags>]`.
  - [ ] Apply in-place edit via patch with confirmation.
  - [ ] **Tests**: Confirm fields are updated correctly and diff is shown before write.
- [ ] **Delete**: Implement `codex mem:delete <id> [--yes]`.
  - [ ] Mark entry archived with `ttl: "0d"` or remove on confirmation.
  - [ ] **Tests**: Verify deletion behavior with and without `--yes` flag.
- [ ] **Compact**: Implement `codex mem:compact` to remove expired entries and enforce max_snippets.
  - [ ] **Tests**: Ensure TTL entries are removed and file stays under size limits.
- [ ] **Lint**: Implement `codex mem:lint` to catch malformed YAML, duplicate ids, missing sections, or overlong files.
  - [ ] **Tests**: Cover malformed front matter, duplicate ids, and over‑200‑line files.

## CLI - Task Commands
- [ ] **Bind**: Implement `codex mem:task bind <ID>` to set active task and create journal file.
  - [ ] **Tests**: Verify binding creates `.codex/tasks/<ID>.md` and updates CODEX shard.
- [ ] **Checkpoint**: Implement `codex mem:task checkpoint "<note>"`.
  - [ ] **Tests**: Append note to task journal with timestamp.
- [ ] **Next**: Implement `codex mem:task next "<bullets>"` to record next steps.
  - [ ] **Tests**: Ensure bullets are written and preserved across sessions.
- [ ] **Sync**: Implement `codex mem:task sync` to reconcile task shard in CODEX.md with journal.
  - [ ] **Tests**: Detect drift and update accordingly.
- [ ] **Complete**: Implement `codex mem:task complete` to mark task done and archive journal.
  - [ ] **Tests**: Journal is archived and task status updated.

## CLI - Cross-Repo / Code Commands
- [ ] **Search**: Implement `codex xrepo:search <regex> [--repos list]` using ripgrep across workspace repos.
  - [ ] **Tests**: Stub ripgrep calls and confirm correct repo set.
- [ ] **Edges Refresh**: Implement `codex code:edges refresh` to rebuild `EDGES.md` digest.
  - [ ] **Tests**: Ensure file generated and contains expected links.
- [ ] **Symbols Refresh**: Implement `codex code:symbols refresh` to regenerate `SYMBOLS.md` via ctags.
  - [ ] **Tests**: Verify symbols are parsed and stored.
- [ ] **Hotset Add**: Implement `codex code:hotset add <path> [--reason <...>]` to mark important files.
  - [ ] **Tests**: File is appended with reason and deduplicated.
- [ ] **Snip**: Implement `codex code:snip <path[:L1-L2]>` to capture code snippets into `SNIPPETS/`.
  - [ ] **Tests**: Snippet saved with correct line numbers and reference.
- [ ] **Compact**: Implement `codex code:compact` to prune old digests/snippets.
  - [ ] **Tests**: Old digests are removed and metrics logged.

## MCP Methods
- [ ] **mem.search**: Expose search as `mem.search({q, scope?, k?})`.
  - [ ] **Tests**: Unit tests for correct result format and scope handling.
- [ ] **mem.add**: Expose add as `mem.add({scope, section, entry})`.
  - [ ] **Tests**: Ensure returned id matches stored entry and redaction occurs.
- [ ] **mem.update**: Expose update as `mem.update({scope, id, patch})`.
  - [ ] **Tests**: Verify fields patched and diff confirmed.
- [ ] **mem.delete**: Expose delete as `mem.delete({scope, id, confirm})`.
  - [ ] **Tests**: Confirm deletion requires confirmation and archives entry.
- [ ] **mem.task.bind**: Implement task binding via MCP.
  - [ ] **Tests**: Journal created and active task recorded.
- [ ] **mem.task.checkpoint**: Implement checkpoint with optional next steps.
  - [ ] **Tests**: Note and next steps appended with timestamps.
- [ ] **code.edges.refresh**: MCP method returning path to `EDGES.md`.
  - [ ] **Tests**: Trigger digest rebuild and return correct path.
- [ ] **code.symbols.refresh**: MCP method for `SYMBOLS.md`.
  - [ ] **Tests**: Confirm symbols file generated.
- [ ] **code.snip**: MCP method to extract snippet.
  - [ ] **Tests**: Validate snippet path and content range.

## Shared Utilities & Testing
- [ ] Implement CODEX.md parser and writer per schema.
  - [ ] **Tests**: Malformed YAML, duplicate ids, TTL handling, performance (≤5ms on 200 lines).
- [ ] Implement redaction filter for emails, API keys, tokens.
  - [ ] **Tests**: Ensure sensitive strings are removed before write.
- [ ] Setup continuous integration with `pytest` running all test suites.

