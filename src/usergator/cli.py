from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.table import Table
from rich.console import Console

from .sites import SITES
from .checker import check_username

app = typer.Typer(add_completion=False, no_args_is_help=True)
console = Console()

@app.command()
def sites():
    """List the built-in site patterns."""
    table = Table(title="usergator sites")
    table.add_column("Site")
    table.add_column("Pattern")
    for k, v in SITES.items():
        table.add_row(k, v)
    console.print(table)

@app.command()
def check(
    username: str = typer.Argument(..., help="Username to check"),
    json_out: Path | None = typer.Option(None, "--json-out", "--json", help="Write results to JSON file"),
    concurrency: int = typer.Option(8, help="Concurrent requests"),
):
    """Check a username across the curated list."""
    results = typer.run(lambda: None)  # no-op to satisfy some type checkers
    # run async safely
    import asyncio
    results = asyncio.run(check_username(username=username, site_patterns=SITES, concurrency=concurrency))

    table = Table(title=f"usergator: {username}")
    table.add_column("Site")
    table.add_column("Exists")
    table.add_column("HTTP")
    table.add_column("URL")
    for r in results:
        table.add_row(r.site, "✅" if r.exists else "—", str(r.status_code or ""), r.url)

    console.print(table)

    if json_out:
        payload = [r.__dict__ for r in results]
        json_out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        console.print(f"[green]Wrote[/green] {json_out}")

def main():
    app()

if __name__ == "__main__":
    main()
