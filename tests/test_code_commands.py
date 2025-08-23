from pathlib import Path
import sys
from click.testing import CliRunner
from datetime import datetime, timedelta
import subprocess
import os

sys.path.append(str(Path(__file__).resolve().parents[1]))
from codex.cli import cli


def test_code_edges_refresh():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("a.md").write_text("[link](b.md)\n")
        Path("b.md").write_text("")
        result = runner.invoke(cli, ["code:edges", "refresh"])
        assert result.exit_code == 0
        assert "a.md -> b.md" in Path("EDGES.md").read_text()


def test_code_symbols_refresh(monkeypatch):
    def fake_run(cmd, capture_output=False, text=False, check=False):
        class R:
            stdout = "foo\tfoo.py\t1\nBar\tbar.py\t2\n"
        return R()

    monkeypatch.setattr(subprocess, "run", fake_run)
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["code:symbols", "refresh"])
        assert result.exit_code == 0
        content = Path("SYMBOLS.md").read_text()
        assert "foo foo.py:1" in content
        assert "Bar bar.py:2" in content


def test_code_hotset_add():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["code:hotset", "add", "file1.py", "--reason", "important"])
        assert result.exit_code == 0
        result = runner.invoke(cli, ["code:hotset", "add", "file1.py", "--reason", "new"])
        lines = Path("HOTSET.md").read_text().splitlines()
        assert lines == ["file1.py - new"]


def test_code_snip_and_compact():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("sample.py").write_text("line1\nline2\nline3\n")
        result = runner.invoke(cli, ["code:snip", "sample.py:1-2"])
        assert result.exit_code == 0
        snip_path = Path(result.output.strip())
        assert snip_path.exists()
        assert snip_path.read_text() == "line1\nline2\n"
        old_time = (datetime.now() - timedelta(days=40)).timestamp()
        os.utime(snip_path, (old_time, old_time))
        result = runner.invoke(cli, ["code:compact"])
        assert "Removed 1 old snippets" in result.output
        assert not snip_path.exists()
