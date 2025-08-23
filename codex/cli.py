from __future__ import annotations

from pathlib import Path

import click

from .memory import search_codex


def resolve_codex_path(scope: str) -> Path:
    if scope == "global":
        return Path.home() / ".codex" / "memory" / "CODEX.md"
    # default project scope
    return Path(".codex") / "CODEX.md"


@click.group()
def cli() -> None:
    """Codex command line interface."""


@cli.command("mem:search")
@click.argument("query")
@click.option("--scope", default="project", type=click.Choice(["project", "global", "module"]))
@click.option("--k", default=5, type=int)
def mem_search(query: str, scope: str, k: int) -> None:
    """Search CODEX memories."""
    path = resolve_codex_path(scope)
    if not path.exists():
        click.echo(f"No CODEX.md found for scope '{scope}' at {path}")
        return
    results = search_codex(path, query, k)
    for e in results:
        tags = f" [{', '.join(e.tags)}]" if e.tags else ""
        click.echo(f"[{e.section}] ({e.id}) {e.text}{tags}")


if __name__ == "__main__":
    cli()
