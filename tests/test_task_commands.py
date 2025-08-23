from click.testing import CliRunner
from pathlib import Path
import re

from codex.cli import cli


def test_task_commands_flow():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["mem:task", "bind", "T1"])
        assert result.exit_code == 0
        journal = Path(".codex/tasks/T1.md")
        assert journal.exists()
        assert Path(".codex/tasks/active").read_text().strip() == "T1"
        codex_content = Path(".codex/CODEX.md").read_text()
        assert "- id: T1" in codex_content

        result = runner.invoke(cli, ["mem:task", "checkpoint", "note"])
        assert result.exit_code == 0
        text = journal.read_text()
        assert "note" in text
        assert re.search(r"\d{4}-\d{2}-\d{2}T", text)

        result = runner.invoke(cli, ["mem:task", "next", "step one;step two"])
        assert result.exit_code == 0
        lines = journal.read_text().splitlines()
        assert "* step one" in lines
        assert "* step two" in lines

        result = runner.invoke(cli, ["mem:task", "sync"])
        assert result.exit_code == 0
        codex_content = Path(".codex/CODEX.md").read_text()
        assert "* step two" in codex_content

        result = runner.invoke(cli, ["mem:task", "complete"])
        assert result.exit_code == 0
        assert not Path(".codex/tasks/active").exists()
        assert Path(".codex/tasks/archive/T1.md").exists()
        codex_content = Path(".codex/CODEX.md").read_text()
        assert 'ttl: "0d"' in codex_content
