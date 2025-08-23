from __future__ import annotations

from pathlib import Path
import sys

from click.testing import CliRunner

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from codex.cli import cli


def test_mem_delete_marks_ttl_with_confirmation():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path('.codex').mkdir()
        Path('.codex/CODEX.md').write_text('# CODEX Memory\n\n## Preferences\n- id: pref-one\n  tags: [t]\n  text: "keep"\n')
        result = runner.invoke(cli, ['mem:delete', 'pref-one'], input='y\n')
        assert result.exit_code == 0
        content = Path('.codex/CODEX.md').read_text()
        assert 'ttl: "0d"' in content


def test_mem_delete_yes_skips_prompt():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path('.codex').mkdir()
        Path('.codex/CODEX.md').write_text('# CODEX Memory\n\n## Preferences\n- id: pref-one\n  tags: [t]\n  text: "keep"\n')
        result = runner.invoke(cli, ['mem:delete', 'pref-one', '--yes'])
        assert result.exit_code == 0
        assert 'Apply delete?' not in result.output
        content = Path('.codex/CODEX.md').read_text()
        assert 'ttl: "0d"' in content
