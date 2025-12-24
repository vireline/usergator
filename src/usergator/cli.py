from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

from .checker import check_username
from .sites import SITES

app = typer.Typer(add_completion=False, help="OSINT username footprint investigator")
console = Console()


@app.command()
def sites() -> None:
    """List the built-in site patterns."""
    table = Table(title="usergator • sources", header_style="bold magenta")
    table.add_column("Site", style="bold")
    table.add_column("Pattern", style="dim")
    for s in SITES:
        table.add_row(s.name, s.url)
    console.print(table)


@app.command()
def check(
    username: str = typer.Argument(..., help="Username to check"),
    json_out: Path | None = typer.Option(
        None, "--json-out", "--json", help="Write results to JSON file"
    ),
    concurrency: int = typer.Option(8, "--concurrency", min=1, max=64, help="Concurrent requests"),
) -> None:
    """Check a username across the curated list."""
    console.print(f"\n[bold cyan]usergator[/bold cyan]  scanning  [bold]{username}[/bold]  ([dim]{len(SITES)} sites[/dim])\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("checking…", total=len(SITES))
        results = []
        for item in check_username(username, concurrency=concurrency):
            results.append(item)
            progress.advance(task)

    # Pretty table
    table = Table(title=None, header_style="bold magenta")
    table.add_column("Site", style="bold")
    table.add_column("URL", overflow="fold", style="dim")
    table.add_column("Status", justify="center")

    def fmt(status: str) -> str:
        s = (status or "").upper()
        if s == "FOUND":
            return "[bold green]FOUND[/bold green]"
        if s == "NOT_FOUND":
            return "[dim]NOT FOUND[/dim]"
        return "[yellow]UNKNOWN[/yellow]"

    found = 0
    not_found = 0
    unknown = 0

    for r in results:
        status = (r.get("status") or "UNKNOWN").upper()
        if status == "FOUND":
            found += 1
        elif status == "NOT_FOUND":
            not_found += 1
        else:
            unknown += 1

        table.add_row(r.get("site", "?"), r.get("url", ""), fmt(status))

    console.print(table)
    console.print(
        f"[green]FOUND[/green]: {found}   "
        f"[dim]NOT FOUND[/dim]: {not_found}   "
        f"[yellow]UNKNOWN[/yellow]: {unknown}\n"
    )

    if json_out:
        json_out.write_text(json.dumps(results, indent=2), encoding="utf-8")
        console.print(f"[dim]Saved →[/dim] [bold]{json_out}[/bold]\n")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
