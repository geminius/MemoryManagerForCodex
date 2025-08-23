from __future__ import annotations

import math
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Dict, Optional

import yaml


SECTION_WEIGHTS: Dict[str, float] = {
    "Preferences": 1.0,
    "Project Facts": 1.2,
    "Guardrails": 1.5,
    "Playbooks": 1.0,
    "Open Questions": 0.8,
}


@dataclass
class Entry:
    id: str
    section: str
    tags: List[str]
    text: str
    updated: Optional[str] = None


TOKEN_RE = re.compile(r"\w+")


def tokenize(s: str) -> List[str]:
    return TOKEN_RE.findall(s.lower())


RE_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
RE_SECRET = re.compile(r"[A-Za-z0-9]{20,}")


def redact(text: str) -> str:
    """Redact obvious secrets like emails and long tokens."""
    text = RE_EMAIL.sub("<redacted:email>", text)
    text = RE_SECRET.sub("<redacted:secret>", text)
    return text


def load_codex_entries(path: Path) -> List[Entry]:
    """Parse CODEX.md into entries."""
    entries: List[Entry] = []
    if not path.exists():
        return entries

    lines = path.read_text().splitlines()
    section: Optional[str] = None
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
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
                if next_line.strip() == "":
                    entry_lines.append(next_line)
                    i += 1
                    continue
                entry_lines.append(next_line)
                i += 1
            data = yaml.safe_load("\n".join(entry_lines))
            if isinstance(data, list) and data:
                raw = data[0]
                entry = Entry(
                    id=str(raw.get("id", "")),
                    section=section or "",
                    tags=[str(t) for t in raw.get("tags", [])],
                    text=str(raw.get("text", "")),
                    updated=raw.get("updated"),
                )
                entries.append(entry)
        else:
            i += 1
    return entries


def score_entry(entry: Entry, query_tokens: Iterable[str]) -> float:
    entry_tokens = set(
        tokenize(entry.id) + entry.tags + tokenize(entry.text[:128])
    )
    matches = sum(1 for t in query_tokens if t in entry_tokens)
    if matches == 0:
        return 0.0
    weight = SECTION_WEIGHTS.get(entry.section, 1.0)
    recency = 1.0
    if entry.updated:
        try:
            dt = datetime.fromisoformat(entry.updated)
            age_days = (datetime.now() - dt).days
            recency = 1 / math.sqrt(1 + age_days)
        except Exception:
            pass
    return matches * weight * recency


def search_codex(path: Path, query: str, k: int = 5) -> List[Entry]:
    entries = load_codex_entries(path)
    tokens = tokenize(query)
    scored = [
        (score_entry(e, tokens), e) for e in entries
    ]
    scored = [se for se in scored if se[0] > 0]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [e for _, e in scored[:k]]
