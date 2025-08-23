from pathlib import Path
import sys
import subprocess

sys.path.append(str(Path(__file__).resolve().parents[1]))
from codex import mcp


def test_mem_search_and_add(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result_id = mcp.mem_add({
        "scope": "project",
        "section": "Project Facts",
        "entry": {"id": "a1", "tags": ["t"], "text": "hello world"},
    })
    assert result_id == "a1"
    results = mcp.mem_search({"q": "hello"})
    assert results[0]["id"] == "a1"


def test_mem_update_and_delete(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    mcp.mem_add({
        "scope": "project",
        "section": "Preferences",
        "entry": {"id": "u1", "tags": [], "text": "old"},
    })
    ok = mcp.mem_update({"id": "u1", "patch": {"text": "new", "tags": ["x"]}})
    assert ok
    content = Path(".codex/CODEX.md").read_text()
    assert "new" in content
    assert "x" in content
    assert "updated" in content
    # delete requires confirmation
    assert not mcp.mem_delete({"id": "u1"})
    assert mcp.mem_delete({"id": "u1", "confirm": True})
    content = Path(".codex/CODEX.md").read_text()
    assert 'ttl: "0d"' in content


def test_mem_add_redaction(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    mcp.mem_add({
        "section": "Guardrails",
        "entry": {"id": "r1", "tags": [], "text": "email test@example.com"},
    })
    content = Path(".codex/CODEX.md").read_text()
    assert "<redacted:email>" in content


def test_task_bind_and_checkpoint(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    journal_path = mcp.mem_task_bind({"id": "T1"})
    assert Path(journal_path).exists()
    mcp.mem_task_checkpoint({"note": "did", "next": ["n1"]})
    text = Path(journal_path).read_text()
    assert "did" in text
    assert "* n1" in text


def test_code_edges_refresh(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path("a.md").write_text("[link](b.md)\n")
    Path("b.md").write_text("")
    out = mcp.code_edges_refresh()
    assert Path(out).exists()
    assert "a.md -> b.md" in Path(out).read_text()


def test_code_symbols_refresh(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    def fake_run(cmd, capture_output=False, text=False, check=False):
        class R:
            stdout = "foo\tfoo.py\t1\nBar\tbar.py\t2\n"
        return R()
    monkeypatch.setattr(subprocess, "run", fake_run)
    out = mcp.code_symbols_refresh()
    content = Path(out).read_text()
    assert "foo foo.py:1" in content
    assert "Bar bar.py:2" in content


def test_code_snip(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path("sample.py").write_text("line1\nline2\nline3\n")
    out = mcp.code_snip({"path": "sample.py", "start": 1, "end": 2})
    p = Path(out)
    assert p.exists()
    assert p.read_text() == "line1\nline2\n"
