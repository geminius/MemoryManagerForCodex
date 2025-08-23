from __future__ import annotations

from pathlib import Path
import difflib
from datetime import datetime
from typing import Optional
import re
import subprocess

import click
import yaml

from .memory import search_codex, redact, load_codex_entries


def resolve_codex_path(scope: str) -> Path:
    if scope == "global":
        return Path.home() / ".codex" / "memory" / "CODEX.md"
    # default project scope
    return Path(".codex") / "CODEX.md"


@click.group()
def cli() -> None:
    """Codex command line interface."""


@cli.command("mem:search")
@click.argument("query")
@click.option("--scope", default="project", type=click.Choice(["project", "global", "module"]))
@click.option("--k", default=5, type=int)
def mem_search(query: str, scope: str, k: int) -> None:
    """Search CODEX memories."""
    path = resolve_codex_path(scope)
    if not path.exists():
        click.echo(f"No CODEX.md found for scope '{scope}' at {path}")
        return
    results = search_codex(path, query, k)
    for e in results:
        tags = f" [{', '.join(e.tags)}]" if e.tags else ""
        click.echo(f"[{e.section}] ({e.id}) {e.text}{tags}")


@cli.command("mem:add")
@click.argument("section")
@click.option("--id", "id_", required=True)
@click.option("--tags", default="", help="Comma-separated tags")
@click.option("--text", required=True)
@click.option("--scope", default="project", type=click.Choice(["project", "global", "module"]))
def mem_add(section: str, id_: str, tags: str, text: str, scope: str) -> None:
    """Add an entry to CODEX.md."""
    path = resolve_codex_path(scope)
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_name(path.name + ".lock")
    try:
        lock_path.open("x").close()
    except FileExistsError:
        click.echo(f"Lock file exists at {lock_path}")
        return
    try:
        original = "# CODEX Memory\n" if not path.exists() else path.read_text()
        if not original.endswith("\n"):
            original += "\n"
        lines = original.splitlines()
        section_header = f"## {section}"
        if section_header not in lines:
            if lines and lines[-1] != "":
                lines.append("")
            lines.append(section_header)
        section_index = lines.index(section_header)
        insert_at = section_index + 1
        while insert_at < len(lines) and not lines[insert_at].startswith("## "):
            insert_at += 1
        tags_list = [t.strip() for t in tags.split(",") if t.strip()]
        entry_lines = [
            f"- id: {id_}",
            f"  tags: [{', '.join(tags_list)}]",
            f"  text: \"{redact(text)}\"",
        ]
        lines[insert_at:insert_at] = entry_lines + ([""] if insert_at < len(lines) else [])
        new_text = "\n".join(lines) + "\n"
        diff = "\n".join(
            difflib.unified_diff(
                original.splitlines(),
                new_text.splitlines(),
                fromfile=str(path),
                tofile=str(path),
            )
        )
        click.echo(diff)
        path.write_text(new_text)
    finally:
        lock_path.unlink(missing_ok=True)


@cli.command("mem:update")
@click.argument("id_")
@click.option("--text", required=True)
@click.option("--tags", default="", help="Comma-separated tags")
@click.option("--scope", default="project", type=click.Choice(["project", "global", "module"]))
@click.option("--yes", is_flag=True, default=False, help="Confirm update without prompt")
def mem_update(id_: str, text: str, tags: str, scope: str, yes: bool) -> None:
    """Update an existing entry in CODEX.md."""
    path = resolve_codex_path(scope)
    if not path.exists():
        click.echo(f"No CODEX.md found for scope '{scope}' at {path}")
        return

    original = path.read_text()
    lines = original.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip() == f"- id: {id_}":
            start = i
            break
    if start is None:
        click.echo(f"Entry {id_} not found")
        return

    end = start + 1
    while end < len(lines) and not lines[end].startswith("- id: ") and not lines[end].startswith("## "):
        end += 1

    entry_lines = lines[start:end]
    tags_list = [t.strip() for t in tags.split(",") if t.strip()]

    # indices of fields within entry_lines
    idx_tags = next((i for i, l in enumerate(entry_lines[1:], start=1) if l.startswith("  tags:")), None)
    idx_text = next((i for i, l in enumerate(entry_lines[1:], start=1) if l.startswith("  text:")), None)
    idx_updated = next((i for i, l in enumerate(entry_lines[1:], start=1) if l.startswith("  updated:")), None)

    if tags_list:
        tags_line = f"  tags: [{', '.join(tags_list)}]"
        if idx_tags is not None:
            entry_lines[idx_tags] = tags_line
        else:
            entry_lines.insert(1, tags_line)
            if idx_text is not None:
                idx_text += 1
            if idx_updated is not None:
                idx_updated += 1

    redacted = redact(text)
    text_line = f"  text: \"{redacted}\""
    if idx_text is not None:
        entry_lines[idx_text] = text_line
    else:
        insert_at = 2 if (tags_list or idx_tags is not None) else 1
        entry_lines.insert(insert_at, text_line)
        if idx_updated is not None:
            idx_updated += 1

    updated_line = f"  updated: \"{datetime.now().isoformat()}\""
    if idx_updated is not None:
        entry_lines[idx_updated] = updated_line
    else:
        insert_at = (idx_text if idx_text is not None else len(entry_lines) - 1) + 1
        entry_lines.insert(insert_at, updated_line)

    lines[start:end] = entry_lines
    new_text = "\n".join(lines) + "\n"
    diff = "\n".join(
        difflib.unified_diff(
            original.splitlines(),
            new_text.splitlines(),
            fromfile=str(path),
            tofile=str(path),
        )
    )
    click.echo(diff)
    if yes or click.confirm("Apply changes?", default=False):
        path.write_text(new_text)
    else:
        click.echo("Aborted")


@cli.command("mem:delete")
@click.argument("id_")
@click.option("--scope", default="project", type=click.Choice(["project", "global", "module"]))
@click.option("--yes", is_flag=True, default=False, help="Confirm deletion without prompt")
def mem_delete(id_: str, scope: str, yes: bool) -> None:
    """Soft delete an entry by setting ttl to 0d."""
    path = resolve_codex_path(scope)
    if not path.exists():
        click.echo(f"No CODEX.md found for scope '{scope}' at {path}")
        return

    original = path.read_text()
    lines = original.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip() == f"- id: {id_}":
            start = i
            break
    if start is None:
        click.echo(f"Entry {id_} not found")
        return

    end = start + 1
    while end < len(lines) and not lines[end].startswith("- id: ") and not lines[end].startswith("## "):
        end += 1

    entry_lines = lines[start:end]
    idx_ttl = next((i for i, l in enumerate(entry_lines[1:], start=1) if l.startswith("  ttl:")), None)
    ttl_line = '  ttl: "0d"'
    if idx_ttl is not None:
        entry_lines[idx_ttl] = ttl_line
    else:
        entry_lines.insert(1, ttl_line)

    lines[start:end] = entry_lines
    new_text = "\n".join(lines) + "\n"
    diff = "\n".join(
        difflib.unified_diff(
            original.splitlines(),
            new_text.splitlines(),
            fromfile=str(path),
            tofile=str(path),
        )
    )
    click.echo(diff)
    if yes or click.confirm("Apply delete?", default=False):
        path.write_text(new_text)
    else:
        click.echo("Aborted")


@cli.command("mem:compact")
@click.option("--scope", default="project", type=click.Choice(["project", "global", "module"]))
@click.option("--max-snippets", default=100, type=int)
def mem_compact(scope: str, max_snippets: int) -> None:
    """Remove expired entries and limit total count."""
    path = resolve_codex_path(scope)
    if not path.exists():
        click.echo(f"No CODEX.md found for scope '{scope}' at {path}")
        return

    entries = [e for e in load_codex_entries(path) if e.ttl != "0d"]
    if len(entries) > max_snippets:
        entries = entries[-max_snippets:]

    lines = ["# CODEX Memory", ""]
    current_section = None
    for e in entries:
        if e.section != current_section:
            if current_section is not None:
                lines.append("")
            lines.append(f"## {e.section}")
            current_section = e.section
        lines.append(f"- id: {e.id}")
        lines.append(f"  tags: [{', '.join(e.tags)}]")
        lines.append(f"  text: \"{e.text}\"")
        if e.updated:
            lines.append(f"  updated: \"{e.updated}\"")
        if e.ttl and e.ttl != "0d":
            lines.append(f"  ttl: \"{e.ttl}\"")
        lines.append("")

    new_text = "\n".join(lines).rstrip() + "\n"
    path.write_text(new_text)


@cli.command("mem:lint")
@click.option("--scope", default="project", type=click.Choice(["project", "global", "module"]))
def mem_lint(scope: str) -> None:
    """Validate CODEX.md for common issues."""
    path = resolve_codex_path(scope)
    if not path.exists():
        click.echo(f"No CODEX.md found for scope '{scope}' at {path}")
        return

    lines = path.read_text().splitlines()
    errors = []
    if len(lines) > 200:
        errors.append("File has more than 200 lines")

    ids = set()
    section: Optional[str] = None
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("## "):
            section = line[3:].strip()
            i += 1
            continue
        if line.startswith("- "):
            entry_lines = [line]
            i += 1
            while i < len(lines):
                next_line = lines[i]
                if next_line.startswith("- ") or next_line.startswith("## "):
                    break
                entry_lines.append(next_line)
                i += 1
            try:
                data = yaml.safe_load("\n".join(entry_lines))
            except yaml.YAMLError:
                errors.append(f"Malformed YAML near line {i - len(entry_lines) + 1}")
                continue
            if not isinstance(data, list) or not data:
                errors.append(f"Malformed entry near line {i - len(entry_lines) + 1}")
                continue
            raw = data[0]
            id_ = raw.get("id")
            if not section:
                errors.append(f"Entry {id_} missing section")
            if id_ in ids:
                errors.append(f"Duplicate id: {id_}")
            ids.add(id_)
        else:
            i += 1

    if errors:
        for e in errors:
            click.echo(f"ERROR: {e}")
        raise SystemExit(1)
    else:
        click.echo("No issues found")


@cli.group("mem:task")
def mem_task() -> None:
    """Task management commands."""


@mem_task.command("bind")
@click.argument("id_")
@click.option("--scope", default="project", type=click.Choice(["project", "global", "module"]))
def task_bind(id_: str, scope: str) -> None:
    """Bind to a task and create its journal."""
    codex_path = resolve_codex_path(scope)
    tasks_dir = codex_path.parent / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    journal = tasks_dir / f"{id_}.md"
    if not journal.exists():
        journal.write_text(f"# Task {id_}\n")
    (tasks_dir / "active").write_text(id_)

    if not codex_path.exists():
        codex_path.write_text("# CODEX Memory\n\n")
    lines = codex_path.read_text().splitlines()
    section_header = "## Tasks"
    if section_header not in lines:
        if lines and lines[-1] != "":
            lines.append("")
        lines.append(section_header)
    section_index = lines.index(section_header) + 1
    while section_index < len(lines) and not lines[section_index].startswith("## "):
        if lines[section_index].strip() == f"- id: {id_}":
            codex_path.write_text("\n".join(lines).rstrip() + "\n")
            return
        section_index += 1
    entry_lines = [
        f"- id: {id_}",
        "  tags: []",
        '  text: "Active"',
        "",
    ]
    insert_at = lines.index(section_header) + 1
    while insert_at < len(lines) and not lines[insert_at].startswith("## "):
        insert_at += 1
    lines[insert_at:insert_at] = entry_lines
    codex_path.write_text("\n".join(lines).rstrip() + "\n")


def _active_task_id(codex_path: Path) -> Optional[str]:
    active_file = codex_path.parent / "tasks" / "active"
    if active_file.exists():
        return active_file.read_text().strip()
    return None


@mem_task.command("checkpoint")
@click.argument("note")
@click.option("--scope", default="project", type=click.Choice(["project", "global", "module"]))
def task_checkpoint(note: str, scope: str) -> None:
    """Add a checkpoint note to the active task."""
    codex_path = resolve_codex_path(scope)
    task_id = _active_task_id(codex_path)
    if not task_id:
        click.echo("No active task")
        return
    journal = codex_path.parent / "tasks" / f"{task_id}.md"
    ts = datetime.now().isoformat()
    with journal.open("a") as f:
        f.write(f"{ts} - {note}\n")
    click.echo(f"Checkpoint added to {journal}")


@mem_task.command("next")
@click.argument("bullets")
@click.option("--scope", default="project", type=click.Choice(["project", "global", "module"]))
def task_next(bullets: str, scope: str) -> None:
    """Record next-step bullets for the active task."""
    codex_path = resolve_codex_path(scope)
    task_id = _active_task_id(codex_path)
    if not task_id:
        click.echo("No active task")
        return
    journal = codex_path.parent / "tasks" / f"{task_id}.md"
    with journal.open("a") as f:
        for b in [b.strip() for b in bullets.split(";") if b.strip()]:
            f.write(f"* {b}\n")
    click.echo("Next steps recorded")


@mem_task.command("sync")
@click.option("--scope", default="project", type=click.Choice(["project", "global", "module"]))
def task_sync(scope: str) -> None:
    """Sync active task journal into CODEX.md."""
    codex_path = resolve_codex_path(scope)
    task_id = _active_task_id(codex_path)
    if not task_id:
        click.echo("No active task")
        return
    journal = codex_path.parent / "tasks" / f"{task_id}.md"
    if not journal.exists() or not codex_path.exists():
        click.echo("Nothing to sync")
        return
    last_line = ""
    for line in reversed(journal.read_text().splitlines()):
        if line.strip():
            last_line = line.strip()
            break
    lines = codex_path.read_text().splitlines()
    section_header = "## Tasks"
    if section_header not in lines:
        click.echo("Tasks section missing")
        return
    idx = lines.index(section_header) + 1
    while idx < len(lines) and not lines[idx].startswith("## "):
        if lines[idx].strip() == f"- id: {task_id}":
            j = idx + 1
            while j < len(lines) and not lines[j].startswith("- id:") and not lines[j].startswith("## "):
                if lines[j].startswith("  text:"):
                    lines[j] = f'  text: "{redact(last_line)}"'
                    break
                j += 1
            else:
                lines.insert(idx + 1, f'  text: "{redact(last_line)}"')
            codex_path.write_text("\n".join(lines).rstrip() + "\n")
            click.echo("Synced")
            return
        idx += 1
    click.echo("Task not found in CODEX.md")


@mem_task.command("complete")
@click.option("--scope", default="project", type=click.Choice(["project", "global", "module"]))
def task_complete(scope: str) -> None:
    """Mark active task complete and archive journal."""
    codex_path = resolve_codex_path(scope)
    task_id = _active_task_id(codex_path)
    if not task_id:
        click.echo("No active task")
        return
    tasks_dir = codex_path.parent / "tasks"
    journal = tasks_dir / f"{task_id}.md"
    archive = tasks_dir / "archive"
    archive.mkdir(exist_ok=True)
    if journal.exists():
        journal.rename(archive / f"{task_id}.md")
    active_file = tasks_dir / "active"
    active_file.unlink(missing_ok=True)

    if codex_path.exists():
        lines = codex_path.read_text().splitlines()
        section_header = "## Tasks"
        if section_header in lines:
            idx = lines.index(section_header) + 1
            while idx < len(lines) and not lines[idx].startswith("## "):
                if lines[idx].strip() == f"- id: {task_id}":
                    j = idx + 1
                    ttl_line = '  ttl: "0d"'
                    while j < len(lines) and not lines[j].startswith("- id:") and not lines[j].startswith("## "):
                        if lines[j].startswith("  ttl:"):
                            lines[j] = ttl_line
                            break
                        j += 1
                    else:
                        lines.insert(idx + 1, ttl_line)
                    codex_path.write_text("\n".join(lines).rstrip() + "\n")
                    break
    click.echo("Task completed")


@cli.command("xrepo:search")
@click.argument("regex")
@click.option("--repos", default="", help="Comma-separated list of repo paths")
def xrepo_search(regex: str, repos: str) -> None:
    """Search across multiple repositories using ripgrep."""
    repo_list = [r.strip() for r in repos.split(",") if r.strip()] or [str(Path.cwd())]
    for repo in repo_list:
        click.echo(f"# {repo}")
        subprocess.run(["rg", regex], cwd=repo, check=False)


@cli.group("code:edges")
def code_edges() -> None:
    """Edge digest commands."""


@code_edges.command("refresh")
def code_edges_refresh() -> None:
    """Rebuild EDGES.md from markdown links."""
    root = Path.cwd()
    edges = []
    link_re = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for md in root.rglob("*.md"):
        if md.name in {"CODEX.md", "EDGES.md", "SYMBOLS.md"}:
            continue
        text = md.read_text()
        for match in link_re.findall(text):
            edges.append(f"{md.relative_to(root)} -> {match}")
    Path("EDGES.md").write_text("# EDGES\n" + "\n".join(edges) + ("\n" if edges else ""))
    click.echo("EDGES.md refreshed")


@cli.group("code:symbols")
def code_symbols() -> None:
    """Symbol index commands."""


@code_symbols.command("refresh")
def code_symbols_refresh() -> None:
    """Regenerate SYMBOLS.md via ctags."""
    result = subprocess.run(
        ["ctags", "-R", "--fields=+n", "-f", "-"], capture_output=True, text=True, check=False
    )
    symbols = []
    for line in result.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) >= 3:
            name, file, line_no = parts[:3]
            symbols.append(f"{name} {file}:{line_no}")
    Path("SYMBOLS.md").write_text("# SYMBOLS\n" + "\n".join(symbols) + ("\n" if symbols else ""))
    click.echo("SYMBOLS.md refreshed")


@cli.group("code:hotset")
def code_hotset() -> None:
    """Hotset management."""


@code_hotset.command("add")
@click.argument("path")
@click.option("--reason", default="", help="Reason for inclusion")
def code_hotset_add(path: str, reason: str) -> None:
    """Add a file to HOTSET.md with optional reason."""
    hotset_path = Path("HOTSET.md")
    entries = {}
    if hotset_path.exists():
        for line in hotset_path.read_text().splitlines():
            if " - " in line:
                p, r = line.split(" - ", 1)
                entries[p] = r
    entries[path] = reason
    with hotset_path.open("w") as f:
        for p, r in entries.items():
            f.write(f"{p} - {r}\n")
    click.echo(f"Added {path}")


@cli.command("code:snip")
@click.argument("spec")
def code_snip(spec: str) -> None:
    """Capture code snippet into SNIPPETS/."""
    if ":" in spec:
        file_part, range_part = spec.split(":", 1)
        m = re.match(r"L?(\d+)(?:-L?(\d+))?", range_part)
        if m:
            start = int(m.group(1))
            end = int(m.group(2) or m.group(1))
        else:
            start = 1
            end = None
    else:
        file_part = spec
        start = 1
        end = None
    file_path = Path(file_part)
    lines = file_path.read_text().splitlines()
    if end is None or end > len(lines):
        end = len(lines)
    snippet = "\n".join(lines[start - 1 : end]) + "\n"
    out_dir = Path("SNIPPETS")
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"{file_path.name}_{start}-{end}.txt"
    out_path.write_text(snippet)
    click.echo(str(out_path))


@cli.command("code:compact")
def code_compact() -> None:
    """Prune old snippets."""
    now = datetime.now().timestamp()
    removed = 0
    snippets_dir = Path("SNIPPETS")
    if snippets_dir.exists():
        for f in snippets_dir.iterdir():
            age_days = (now - f.stat().st_mtime) / 86400
            if age_days > 30:
                f.unlink()
                removed += 1
    click.echo(f"Removed {removed} old snippets")

if __name__ == "__main__":
    cli()
