from __future__ import annotations

from pathlib import Path
import time

import pytest

from codex.memory import Entry, load_codex_entries, write_codex_entries


def test_load_codex_entries_malformed_yaml(tmp_path: Path) -> None:
    p = tmp_path / "CODEX.md"
    # unterminated quote triggers YAML error
    p.write_text("# CODEX\n\n## Sec\n- id: a\n  text: \"unterminated")
    with pytest.raises(ValueError):
        load_codex_entries(p)


def test_load_codex_entries_duplicate_ids(tmp_path: Path) -> None:
    p = tmp_path / "CODEX.md"
    p.write_text(
        "# CODEX\n\n## Sec\n- id: a\n  text: one\n- id: a\n  text: two\n"
    )
    with pytest.raises(ValueError):
        load_codex_entries(p)


def test_load_codex_entries_ttl_handling(tmp_path: Path) -> None:
    p = tmp_path / "CODEX.md"
    p.write_text(
        "# CODEX\n\n## Sec\n- id: keep\n  text: ok\n- id: expire\n  text: gone\n  ttl: \"0d\"\n"
    )
    entries = load_codex_entries(p)
    ids = [e.id for e in entries]
    assert ids == ["keep"]


def test_load_codex_entries_performance(tmp_path: Path) -> None:
    p = tmp_path / "CODEX.md"
    lines = ["# CODEX", "", "## Sec"]
    for i in range(66):  # roughly >200 lines
        lines.extend([f"- id: e{i}", "  text: sample", ""])
    p.write_text("\n".join(lines))
    start = time.perf_counter()
    load_codex_entries(p)
    duration = time.perf_counter() - start
    assert duration < 0.05


def test_write_codex_entries_roundtrip(tmp_path: Path) -> None:
    p = tmp_path / "CODEX.md"
    entries = [
        Entry(id="a", section="Sec", tags=["t"], text="hello"),
        Entry(id="b", section="Sec", tags=[], text="bye", ttl="1d"),
    ]
    write_codex_entries(p, entries)
    loaded = load_codex_entries(p)
    assert [e.id for e in loaded] == ["a", "b"]
    assert loaded[0].text == "hello"
    assert loaded[1].ttl == "1d"
