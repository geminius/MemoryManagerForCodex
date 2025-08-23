from click.testing import CliRunner
from codex.cli import cli
from pathlib import Path
import subprocess


def test_xrepo_search_runs_on_repos(monkeypatch):
    calls = []

    def fake_run(cmd, cwd=None, check=False):
        calls.append((cmd, cwd))
        class R:
            returncode = 0
        return R()

    monkeypatch.setattr(subprocess, "run", fake_run)

    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("repo1").mkdir()
        Path("repo2").mkdir()
        result = runner.invoke(cli, ["xrepo:search", "foo", "--repos", "repo1,repo2"])
        assert result.exit_code == 0
        assert calls == [(["rg", "foo"], "repo1"), (["rg", "foo"], "repo2")]
