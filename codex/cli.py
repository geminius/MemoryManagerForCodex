from __future__ import annotations

from pathlib import Path
import difflib
from datetime import datetime
from typing import Optional

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
def mem_update(id_: str, text: str, tags: str, scope: str) -> None:
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
    if click.confirm("Apply changes?", default=False):
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


if __name__ == "__main__":
    cli()
