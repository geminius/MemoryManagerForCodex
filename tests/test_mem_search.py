from __future__ import annotations

from pathlib import Path
import sys

from click.testing import CliRunner

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from codex.cli import cli


PROJECT_CODEX = """# CODEX Memory

## Preferences
- id: pref-js-style
  tags: [style, js]
  text: "Use 2-space indent; no semicolons."

## Guardrails
- id: guard-db
  tags: [safety, db]
  text: "Never run destructive migrations."

## Project Facts
- id: fact-one
  tags: [project]
  text: "project uses microservices"
- id: fact-two
  tags: [project]
  text: "project uses database"
"""

GLOBAL_CODEX = """# CODEX Memory

## Project Facts
- id: global-fact
  tags: [global]
  text: "global memory entry"
"""


def test_search_returns_section_and_entry():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path('.codex').mkdir()
        Path('.codex/CODEX.md').write_text(PROJECT_CODEX)
        result = runner.invoke(cli, ['mem:search', 'indent'])
        assert 'pref-js-style' in result.output
        assert '[Preferences]' in result.output
        assert result.exit_code == 0


def test_scope_and_k_limit():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path('.codex').mkdir()
        Path('.codex/CODEX.md').write_text(PROJECT_CODEX)
        home = Path('home')
        (home / '.codex/memory').mkdir(parents=True)
        (home / '.codex/memory/CODEX.md').write_text(GLOBAL_CODEX)
        env = {'HOME': str(home)}
        result = runner.invoke(cli, ['mem:search', 'global', '--scope', 'global'], env=env)
        assert 'global-fact' in result.output
        assert '[Project Facts]' in result.output
        result = runner.invoke(cli, ['mem:search', 'project', '--k', '1'], env=env)
        lines = [l for l in result.output.strip().splitlines() if l]
        assert len(lines) == 1


def test_missing_file_handled():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ['mem:search', 'anything'])
        assert 'No CODEX.md found' in result.output
        assert result.exit_code == 0
