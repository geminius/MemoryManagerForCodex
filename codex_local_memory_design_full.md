# Codex CLI — Local Filesystem Persistent Memory (Claude-Style)

**Version:** 0.1 • **Author:** Xiao (AI Expert) • **Date:** 2025-08-23

Goal: Design a **local-first, zero-database** memory system for Codex CLI that provides Claude-style cross-session memory, task tracking, and cross-repository code navigation—implemented entirely with **Markdown and simple files**.

---

## 0) Scope & Principles

- **Plain files only:** Markdown + small YAML where needed.
- **Deterministic structure:** strict schema for quick parsing.
- **Short & curated:** keep memory files small (≤200 lines).
- **Explicit writes:** dry-run diffs and user confirmation.
- **Scoped isolation:** module → project → global; no cross-pollution unless imported.

---

## 1) File Layout

```
Global   : ~/.codex/memory/CODEX.md
Project  : <repo>/.codex/CODEX.md
Module   : <repo>/<subdir>/.codex/CODEX.md   # optional
Config   : <repo>/.codex/memory.toml
Tasks    : <repo>/.codex/tasks/<TASK-ID>.md  # per-task journals
Digests  : <repo>/.codex/digests/{MODULES.md,SYMBOLS.md,IMPORTS.md,EDGES.md,HOTSET.md,SNIPPETS/}
Workspace: ~/.codex/memory/workspace.yaml    # list of repos for cross-repo ops
```

---

## 2) Markdown Schema (CODEX.md)

Each scope uses a single **CODEX.md** with front-matter and fixed sections. Entries are list items with `id`, `tags`, and `text` (single line or block).

```yaml
---
version: 1
scope: project            # global | project | module
updated: 2025-08-23
owner: "@xiao"
max_snippets: 5
---
```

```markdown
# CODEX Memory

## Preferences
- id: pref-js-style
  tags: [style, js]
  text: "Use 2-space indent; no semicolons."

## Project Facts
- id: fact-arch-edges
  tags: [architecture]
  text: "Service A publishes to Kafka topic `orders.v1`; Service B subscribes."

## Guardrails
- id: guard-db
  tags: [safety, db]
  text: "Never run destructive migrations without --dry-run and approval."

## Playbooks
- id: pb-test-db
  tags: [testing, db]
  text: |
    Local DB reset:
    1) docker compose down -v
    2) docker compose up -d db
    3) psql -f schema.sql

## Open Questions
- id: oq-caching
  tags: [decision, caching]
  text: "Which cache invalidation policy are we standardizing on?"
```

---

## 3) Retrieval (No Database)

An ephemeral in-memory index is built on demand from each CODEX.md: tokens from `id`, `tags`, and first 128 chars of `text`. Section weights steer relevance. Default cap: top-5 diversified snippets.

```
score(entry) = α·keyword + β·sectionWeight + γ·recencyBoost + δ·priority
where recencyBoost = 1 / sqrt(1 + ageDays)
Diversity: bucket by id prefix; keep 1 per bucket.
```

Injection format (prepended to the model prompt):

```
[Memory from CODEX.md]
- (pref-js-style) Use 2-space indent; no semicolons.  [style, js]
- (guard-db) Never run destructive migrations without --dry-run... [safety, db]
```

---

## 4) Safe Write Path

- **add_entry(section, entry):** append list item in section.
- **update_entry(id, fields):** in-place edit of that list item.
- **delete_entry(id):** remove or mark `ttl: "0d"` and `archived: true`.
- **move_entry(id, section):** remove + add atomically.
- **Dry-run → unified diff → --yes to write.**
- **Lock file `.CODEX.md.lock` during writes** to avoid races.
- **Redaction** of secrets (emails, API keys) pre-write.

---

## 5) Task Tracking from tasks.md (One Chat per Task)

Use `tasks.md` as source of truth, with **per-task journals** and a tiny status shard in CODEX.md. Bind the active chat to a task ID (e.g., `T-147`).

```
<repo>/tasks.md
- [ ] T-147: speed up cold start
  - owner: @xiao
  - repo: app/
  - labels: perf, startup
  - notes: Investigate lazy imports.
```

When binding a task, the tool (a) reads tasks.md, (b) creates/updates `.codex/tasks/T-147.md` (rolling journal), and (c) updates `CODEX.md#Tasks` with 1–3 lines (status + next steps).

```
.codex/tasks/T-147.md
---
task: T-147
repo: .
created: 2025-08-23T09:15:12Z
tasks_digest: <sha256-of-block-in-tasks.md>
---

## 2025-08-23 11:04
- Change: defer prisma init until first query
- Files: app/src/bootstrap.ts, app/src/db.ts
- Evidence: cold-start 3.8s → 2.6s
- Next: flamegraph on dynamic imports
```

CLI (all file-backed):

```
codex mem:task bind T-147
codex mem:task checkpoint "Removed 1.2s by deferring prisma init"
codex mem:task next "- profile module loader
- capture flamegraph"
codex mem:task sync
codex mem:task complete
```

---

## 6) Cross-Repo Dependencies & Large Codebases (No DB)

Create **digests** per repo and a **workspace map** to navigate huge codebases without stuffing the context window. All outputs are Markdown and small.

```
~/.codex/memory/workspace.yaml
repos:
  - name: app
    path: ~/dev/app
  - name: payments
    path: ~/dev/payments
  - name: shared
    path: ~/dev/shared
```

Digest files (generated on demand):

```
<repo>/.codex/digests/
  MODULES.md   # module -> key files, services, exports
  SYMBOLS.md   # symbol -> file, signature, brief doc
  IMPORTS.md   # file -> imports
  EDGES.md     # cross-repo edges
  HOTSET.md    # prioritized files for current task
  SNIPPETS/    # curated small excerpts (<= 60 lines each)
```

Cross-repo flow: use ripgrep/ctags to build digests, then budgeted retrieval selects at most a few lines/snippets to inject. Everything cites file and line range for provenance.

---

## 7) Retrieval Budgeting & Context Discipline

```
memory.toml
[retrieval]
max_snippets = 3
max_snippet_tokens = 200
max_digest_hits = 5
```

At answer time:  
1. always include CODEX.md shards (Tasks/Guardrails/Playbooks)  
2. query digests to pick ≤N candidates  
3. include ≤3 tiny snippets (≤200 tokens each), summarized if needed  

---

## 8) CLI & MCP Interfaces (File-backed)

```
# Memory
codex mem:search "<query>" [--scope project] [--k 5]
codex mem:add Preferences --id pref-python-tests --tags testing,python --text "Prefer pytest fixtures; use factory-boy."
codex mem:update fact-arch-edges --text "A->orders.v2; B subscribes"
codex mem:delete oq-caching --yes
codex mem:compact
codex mem:lint

# Tasks
codex mem:task bind <ID>
codex mem:task checkpoint "<note>"
codex mem:task next "<bullets>"
codex mem:task sync
codex mem:task complete

# Cross-repo / code
codex xrepo:search "<regex>" [--repos app,shared]
codex code:edges refresh
codex code:symbols refresh
codex code:hotset add <path> [--reason "..."]
codex code:snip <path[:L1-L2]>
codex code:compact
```

```
MCP methods:
mem.search({ q, scope?, k? }) -> [ {id, section, text, tags, source} ]
mem.add({ scope, section, entry }) -> { id }
mem.update({ scope, id, patch }) -> { ok }
mem.delete({ scope, id, confirm }) -> { ok }
mem.task.bind({ id }) -> { ok }
mem.task.checkpoint({ id, note, next? }) -> { ok }
code.edges.refresh({ repos? }) -> { path }
code.symbols.refresh({ repos? }) -> { path }
code.snip({ path, range? }) -> { snippetPath }
```

---

## 9) Safety, Privacy, and Ops

- Local-first only; no network unless explicitly enabled in memory.toml.
- File permissions: dirs 0700, files 0600.
- Redaction filter on writes for emails, API keys, tokens.
- Diff-then-confirm for all writes; `.CODEX.md.lock` to prevent races.
- ZDR compliance: if zero-data mode, memory ops are no-ops.
- No background jobs; all maintenance (`compact`, `refresh`) is explicit.

---

## 10) Performance Targets & Testing

- Targets: parse ≤5ms for 200-line CODEX.md; search p95 ≤2ms; end-to-end recall ≤10ms; cross-repo digest refresh (rg+ctags) typically seconds and run on demand.
- Testing: parser (malformed YAML, duplicate ids), retrieval (weights/recency/diversity), writes (diff/lock/redaction), tasks sync (digest drift), digests (edge extraction), perf on 50/100/200-line files.

---

## 11) Risks & Mitigations

- **Stale notes bias answers** — Recency decay; TTL; lint warnings; easy edits via CODEX.md; provenance inline.
- **Secrets accidentally stored** — Redaction + confirmation gates + audit lines in journal headers.
- **Context bloat** — Hard caps (max_snippets/max_hits); summarization of snippets; compact command.
- **Cross-repo drift** — workspace.yaml + verify; digest refresh commands; annotate stale entries.
- **Concurrent edits** — Lock files + unified diff; fail fast if locked; merge guidance.

---

## 12) Quickstart

```
# Initialize
mkdir -p ~/.codex/memory && printf "# CODEX Memory

## Preferences
" > ~/.codex/memory/CODEX.md
mkdir -p ./.codex && printf "# CODEX Memory

## Preferences
" > ./.codex/CODEX.md

# Add a rule
codex mem:add Preferences --id pref-js-style --tags style,js --text "Use 2-space indent; no semicolons."

# Bind a task and checkpoint
codex mem:task bind T-147
codex mem:task checkpoint "Deferrred prisma init; -1.2s cold start"
codex mem:task next "- profile loader
- capture flamegraph"

# Generate cross-repo digests
codex code:edges refresh
codex code:symbols refresh
codex code:snip app/services/customer.ts:120-180
```
