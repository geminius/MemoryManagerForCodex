from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from codex import mcp  # type: ignore


def test_mcp_mem_add_search_update_delete_project_scope(tmp_path: Path, monkeypatch):
    cwd = tmp_path
    monkeypatch.chdir(cwd)
    (cwd / ".codex").mkdir()
    # add
    added_id = mcp.mem_add(
        {
            "scope": "project",
            "section": "Preferences",
            "entry": {"id": "pref-style", "tags": ["style"], "text": "2-space indent"},
        }
    )
    assert added_id == "pref-style"
    codex_path = cwd / ".codex/CODEX.md"
    assert codex_path.exists()
    # search
    hits = mcp.mem_search({"q": "indent", "scope": "project", "k": 5})
    assert any(h["id"] == "pref-style" for h in hits)
    # update
    ok = mcp.mem_update({"scope": "project", "id": "pref-style", "patch": {"text": "no tabs"}})
    assert ok
    text = codex_path.read_text()
    assert "no tabs" in text and "updated:" in text
    # delete requires confirm
    assert mcp.mem_delete({"scope": "project", "id": "pref-style", "confirm": False}) is False
    assert mcp.mem_delete({"scope": "project", "id": "pref-style", "confirm": True}) is True
    assert 'ttl: "0d"' in codex_path.read_text()


def test_mcp_code_edges_symbols_and_snip(tmp_path: Path, monkeypatch):
    cwd = tmp_path
    monkeypatch.chdir(cwd)
    (cwd / "README.md").write_text("See [Guide](docs/guide.md) and [Home](./index.md)\n")
    (cwd / "docs").mkdir()
    (cwd / "docs/guide.md").write_text("Link to [Other](other.md)")

    # edges
    out_edges = mcp.code_edges_refresh({})
    edges_text = (cwd / out_edges).read_text()
    assert "README.md -> docs/guide.md" in edges_text
    assert "docs/guide.md -> other.md" in edges_text

    # symbols (mock ctags)
    class DummyProc:
        stdout = "funcA\tapp.py\t10\nClassB\tx.py\t42\n"
    monkeypatch.setattr(mcp.subprocess, "run", lambda *a, **k: DummyProc())
    out_symbols = mcp.code_symbols_refresh({})
    sym_text = (cwd / out_symbols).read_text()
    assert "funcA app.py:10" in sym_text
    assert "ClassB x.py:42" in sym_text

    # snip
    (cwd / "app.py").write_text("one\nTwo\nTHREE\n")
    out_snip = mcp.code_snip({"path": str(cwd / "app.py"), "start": 2, "end": 3})
    snip_text = (cwd / out_snip).read_text()
    assert snip_text == "Two\nTHREE\n"


def test_mcp_task_bind_and_checkpoint(tmp_path: Path, monkeypatch):
    cwd = tmp_path
    monkeypatch.chdir(cwd)
    # bind creates journal and marks active
    journal_path = mcp.mem_task_bind({"id": "T-1", "scope": "project"})
    j = Path(journal_path)
    assert j.exists()
    # checkpoint appends a line
    checkpoint = mcp.mem_task_checkpoint({"note": "did work", "scope": "project", "next": ["ship it"]})
    assert checkpoint is not None
    text = j.read_text()
    assert "did work" in text and "* ship it" in text
