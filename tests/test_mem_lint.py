from __future__ import annotations

from pathlib import Path
import sys

from click.testing import CliRunner

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from codex.cli import cli


def test_mem_lint_detects_issues():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path('.codex').mkdir()
        content = (
            '# CODEX Memory\n\n'
            '- id: orphan\n  tags: []\n  text: "orphan"\n\n'
            '## Section\n'
            '- id: dup\n  tags: []\n  text: "one"\n'
            '- id: dup\n  tags: []\n  text: "two"\n'
        )
        extra = '\n'.join(['#'] * 190)
        Path('.codex/CODEX.md').write_text(content + extra)
        result = runner.invoke(cli, ['mem:lint'])
        assert result.exit_code != 0
        out = result.output.lower()
        assert 'duplicate id' in out
        assert 'missing section' in out
        assert 'more than 200 lines' in out
