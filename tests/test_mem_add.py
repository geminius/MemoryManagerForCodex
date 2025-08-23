from __future__ import annotations

from pathlib import Path
import sys

from click.testing import CliRunner

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from codex.cli import cli


def test_mem_add_appends_with_diff_and_redaction():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path('.codex').mkdir()
        Path('.codex/CODEX.md').write_text('# CODEX Memory\n\n## Preferences\n')
        cmd = [
            'mem:add',
            'Preferences',
            '--id', 'pref-new',
            '--tags', 'test',
            '--text', 'Reach me at user@example.com with key ABCDEFGHIJKLMNOPQRST',
        ]
        result = runner.invoke(cli, cmd)
        assert result.exit_code == 0
        assert '+- id: pref-new' in result.output
        content = Path('.codex/CODEX.md').read_text()
        assert 'user@example.com' not in content
        assert '<redacted:email>' in content
        assert '<redacted:secret>' in content


def test_mem_add_respects_lock_file():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path('.codex').mkdir()
        Path('.codex/CODEX.md').write_text('# CODEX Memory\n')
        Path('.codex/CODEX.md.lock').write_text('')
        cmd = [
            'mem:add',
            'Preferences',
            '--id', 'pref-blocked',
            '--tags', 't',
            '--text', 'blocked',
        ]
        result = runner.invoke(cli, cmd)
        assert 'lock file exists' in result.output.lower()
        content = Path('.codex/CODEX.md').read_text()
        assert 'pref-blocked' not in content
