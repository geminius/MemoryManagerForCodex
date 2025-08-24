from __future__ import annotations

from pathlib import Path
import os
import sys

from click.testing import CliRunner

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from codex.cli import cli  # type: ignore


def test_task_flow_bind_checkpoint_sync_complete(monkeypatch):
    runner = CliRunner()
    with runner.isolated_filesystem():
        # bind
        result = runner.invoke(cli, ["mem:task", "bind", "T-9"])
        assert result.exit_code == 0
        codex = Path(".codex/CODEX.md")
        assert codex.exists() and "## Tasks" in codex.read_text()
        # checkpoint + next
        r1 = runner.invoke(cli, ["mem:task", "checkpoint", "noted"])
        r2 = runner.invoke(cli, ["mem:task", "next", "a;b"])
        assert r1.exit_code == 0 and r2.exit_code == 0
        # sync into CODEX
        r3 = runner.invoke(cli, ["mem:task", "sync"]) 
        assert r3.exit_code == 0
        text = codex.read_text()
        assert 'text: "' in text  # brief content synced
        # complete archives journal and marks ttl
        r4 = runner.invoke(cli, ["mem:task", "complete"])
        assert r4.exit_code == 0
        archive = Path(".codex/tasks/archive/T-9.md")
        assert archive.exists()
        assert 'ttl: "0d"' in codex.read_text()


def test_code_edges_symbols_snip_and_compact(monkeypatch):
    runner = CliRunner()
    with runner.isolated_filesystem():
        # prepare files
        Path("a.md").write_text("See [B](b.md)")
        Path("b.md").write_text("Hi")
        # edges
        r1 = runner.invoke(cli, ["code:edges", "refresh"]) 
        assert r1.exit_code == 0
        assert Path("EDGES.md").exists()
        # symbols (mock ctags)
        class DummyProc:
            stdout = "name\tfile.py\t7\n"
        import subprocess as _sp
        monkeypatch.setattr(_sp, "run", lambda *a, **k: DummyProc())
        # patch into module by re-importing the command function context
        r2 = runner.invoke(cli, ["code:symbols", "refresh"]) 
        assert r2.exit_code == 0
        assert Path("SYMBOLS.md").exists()
        # snip + compact
        Path("file.py").write_text("one\nTwo\nTHREE\n")
        r3 = runner.invoke(cli, ["code:snip", "file.py:2-3"]) 
        assert r3.exit_code == 0
        out_path = Path(r3.output.strip())
        assert out_path.exists() and out_path.read_text() == "Two\nTHREE\n"
        # make it old and compact
        old = (Path.cwd() / out_path)
        thirty_one_days_secs = 31 * 24 * 3600
        os.utime(old, (old.stat().st_atime - thirty_one_days_secs, old.stat().st_mtime - thirty_one_days_secs))
        r4 = runner.invoke(cli, ["code:compact"]) 
        assert r4.exit_code == 0

