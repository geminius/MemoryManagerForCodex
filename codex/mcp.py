from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import subprocess
import re
from datetime import datetime

from .cli import resolve_codex_path, _active_task_id
from .memory import search_codex, load_codex_entries, redact


def mem_search(params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search CODEX.md memories and return matching entries."""
    q = params["q"]
    scope = params.get("scope", "project")
    k = params.get("k", 5)
    path = resolve_codex_path(scope)
    if not path.exists():
        return []
    results = search_codex(path, q, k)
    return [vars(e) for e in results]


def mem_add(params: Dict[str, Any]) -> str:
    """Add an entry to CODEX.md and return its id."""
    scope = params.get("scope", "project")
    section = params["section"]
    entry = params["entry"]
    id_ = entry["id"]
    tags = entry.get("tags", [])
    text = redact(entry.get("text", ""))
    path = resolve_codex_path(scope)
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "# CODEX Memory\n\n" if not path.exists() else path.read_text()
    if not content.endswith("\n"):
        content += "\n"
    lines = content.splitlines()
    section_header = f"## {section}"
    if section_header not in lines:
        if lines and lines[-1] != "":
            lines.append("")
        lines.append(section_header)
    insert_at = lines.index(section_header) + 1
    while insert_at < len(lines) and not lines[insert_at].startswith("## "):
        insert_at += 1
    entry_lines = [
        f"- id: {id_}",
        f"  tags: [{', '.join(tags)}]",
        f"  text: \"{text}\"",
        "",
    ]
    lines[insert_at:insert_at] = entry_lines
    path.write_text("\n".join(lines).rstrip() + "\n")
    return id_


def mem_update(params: Dict[str, Any]) -> bool:
    """Patch an existing entry in CODEX.md."""
    scope = params.get("scope", "project")
    id_ = params["id"]
    patch = params.get("patch", {})
    path = resolve_codex_path(scope)
    if not path.exists():
        return False
    lines = path.read_text().splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip() == f"- id: {id_}":
            start = i
            break
    if start is None:
        return False
    end = start + 1
    while end < len(lines) and not lines[end].startswith("- id: ") and not lines[end].startswith("## "):
        end += 1
    entry_lines = lines[start:end]
    idx_tags = next((i for i, l in enumerate(entry_lines[1:], start=1) if l.startswith("  tags:")), None)
    idx_text = next((i for i, l in enumerate(entry_lines[1:], start=1) if l.startswith("  text:")), None)
    idx_updated = next((i for i, l in enumerate(entry_lines[1:], start=1) if l.startswith("  updated:")), None)
    if "tags" in patch:
        tags_line = f"  tags: [{', '.join(patch['tags'])}]"
        if idx_tags is not None:
            entry_lines[idx_tags] = tags_line
        else:
            entry_lines.insert(1, tags_line)
            if idx_text is not None:
                idx_text += 1
            if idx_updated is not None:
                idx_updated += 1
    if "text" in patch:
        text_line = f"  text: \"{redact(patch['text'])}\""
        if idx_text is not None:
            entry_lines[idx_text] = text_line
        else:
            insert_at = 2 if ("tags" in patch or idx_tags is not None) else 1
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
    path.write_text("\n".join(lines).rstrip() + "\n")
    return True


def mem_delete(params: Dict[str, Any]) -> bool:
    """Soft delete an entry by setting ttl to 0d. Requires confirmation."""
    scope = params.get("scope", "project")
    id_ = params["id"]
    confirm = params.get("confirm", False)
    if not confirm:
        return False
    path = resolve_codex_path(scope)
    if not path.exists():
        return False
    lines = path.read_text().splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip() == f"- id: {id_}":
            start = i
            break
    if start is None:
        return False
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
    path.write_text("\n".join(lines).rstrip() + "\n")
    return True


def mem_task_bind(params: Dict[str, Any]) -> str:
    """Bind to a task and create its journal."""
    scope = params.get("scope", "project")
    id_ = params["id"]
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
    insert_at = lines.index(section_header) + 1
    while insert_at < len(lines) and not lines[insert_at].startswith("## "):
        if lines[insert_at].strip() == f"- id: {id_}":
            codex_path.write_text("\n".join(lines).rstrip() + "\n")
            return str(journal)
        insert_at += 1
    entry_lines = [
        f"- id: {id_}",
        "  tags: []",
        '  text: "Active"',
        "",
    ]
    lines[insert_at:insert_at] = entry_lines
    codex_path.write_text("\n".join(lines).rstrip() + "\n")
    return str(journal)


def mem_task_checkpoint(params: Dict[str, Any]) -> Optional[str]:
    """Append a checkpoint note and optional next steps to the active task."""
    scope = params.get("scope", "project")
    note = params["note"]
    next_steps = params.get("next", [])
    codex_path = resolve_codex_path(scope)
    task_id = _active_task_id(codex_path)
    if not task_id:
        return None
    journal = codex_path.parent / "tasks" / f"{task_id}.md"
    ts = datetime.now().isoformat()
    with journal.open("a") as f:
        f.write(f"{ts} - {note}\n")
        for step in next_steps:
            f.write(f"* {step}\n")
    return str(journal)


def code_edges_refresh(params: Optional[Dict[str, Any]] = None) -> str:
    """Rebuild EDGES.md from markdown links and return its path."""
    root = Path.cwd()
    edges: List[str] = []
    link_re = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for md in root.rglob("*.md"):
        if md.name in {"CODEX.md", "EDGES.md", "SYMBOLS.md"}:
            continue
        text = md.read_text()
        for target in link_re.findall(text):
            edges.append(f"{md.relative_to(root)} -> {target}")
    Path("EDGES.md").write_text("# EDGES\n" + "\n".join(edges) + ("\n" if edges else ""))
    return str(Path("EDGES.md"))


def code_symbols_refresh(params: Optional[Dict[str, Any]] = None) -> str:
    """Regenerate SYMBOLS.md via ctags and return its path."""
    result = subprocess.run(
        ["ctags", "-R", "--fields=+n", "-f", "-"], capture_output=True, text=True, check=False
    )
    symbols: List[str] = []
    for line in result.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) >= 3:
            name, file, line_no = parts[:3]
            symbols.append(f"{name} {file}:{line_no}")
    Path("SYMBOLS.md").write_text("# SYMBOLS\n" + "\n".join(symbols) + ("\n" if symbols else ""))
    return str(Path("SYMBOLS.md"))


def code_snip(params: Dict[str, Any]) -> str:
    """Capture a code snippet into SNIPPETS/ and return the path."""
    path = Path(params["path"])
    start = params.get("start", 1)
    end = params.get("end")
    lines = path.read_text().splitlines()
    if end is None or end > len(lines):
        end = len(lines)
    snippet = "\n".join(lines[start - 1 : end]) + "\n"
    out_dir = Path("SNIPPETS")
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"{path.name}_{start}-{end}.txt"
    out_path.write_text(snippet)
    return str(out_path)
