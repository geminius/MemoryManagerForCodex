from __future__ import annotations

from pathlib import Path
import sys

from click.testing import CliRunner

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from codex.cli import cli


def test_mem_update_patches_entry_with_confirmation():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path('.codex').mkdir()
        Path('.codex/CODEX.md').write_text('# CODEX Memory\n\n## Preferences\n- id: pref-one\n  tags: [t1]\n  text: "old"\n')
        cmd = [
            'mem:update',
            'pref-one',
            '--text', 'new',
            '--tags', 't2',
        ]
        result = runner.invoke(cli, cmd, input='y\n')
        assert result.exit_code == 0
        # diff shows old and new text
        assert '-  text: "old"' in result.output
        assert '+  text: "new"' in result.output
        content = Path('.codex/CODEX.md').read_text()
        assert 'pref-one' in content
        assert 't2' in content
        assert 'new' in content
        assert 'old' not in content
        assert 'updated:' in content
