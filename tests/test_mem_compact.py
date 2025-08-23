from __future__ import annotations

from pathlib import Path
import sys

from click.testing import CliRunner

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from codex.cli import cli


def test_mem_compact_removes_expired_and_limits():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path('.codex').mkdir()
        content = (
            '# CODEX Memory\n\n## Preferences\n'
            '- id: one\n  tags: []\n  text: "one"\n  ttl: "0d"\n'
            '- id: two\n  tags: []\n  text: "two"\n'
            '- id: three\n  tags: []\n  text: "three"\n'
        )
        Path('.codex/CODEX.md').write_text(content)
        result = runner.invoke(cli, ['mem:compact', '--max-snippets', '1'])
        assert result.exit_code == 0
        text = Path('.codex/CODEX.md').read_text()
        assert 'id: one' not in text
        assert 'id: two' not in text
        assert 'id: three' in text
