from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

import typer
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

from .checker import check_username
from .sites import SITES

app = typer.Typer(add_completion=False, help="OSINT username footprint investigator")
console = Console()


def _iter_sites() -> Iterable[tuple[str, str]]:
    """
    SITES in this project has been edited a few times, so we accept either:
      - list[str] (site names) + URL built elsewhere
      - list[objects] with .name and .url
      - list[tuple(name, url)]
      - dict-like items with keys name/url
    This keeps CLI robust.
    """
    for s in SITES:
        if isinstance(s, tuple) and len(s) == 2:
            yield str(s[0]), str(s[1])
        elif isinstance(s, dict):
            yield str(s.get("name")), str(s.get("url"))
        elif hasattr(s, "name") and hasattr(s, "url"):
            yield str(s.name), str(s.url)
        else:
            # fallback: best effort string + unknown pattern
            yield str(s), ""


@app.command()
def sites() -> None:
    """List the built-in site patterns."""
    table = Table(title="usergator • Username Sources")
    table.add_column("Site", style="bold magenta")
    table.add_column("Pattern", style="dim")
    for name, url in _iter_sites():
        table.add_row(name, url)
    console.print(table)


@app.command()
def check(
    username: str = typer.Argument(..., help="Username to check"),
    json_out: Path | None = typer.Option(
        None, "--json-out", "--json", help="Write results to JSON file"
    ),
    concurrency: int = typer.Option(8, "--concurrency", help="Concurrent requests"),
) -> None:
    """Check a username across the curated list."""
    console.print(
        f"[bold cyan]usergator[/bold cyan] • scanning [bold]{username}[/bold]  "
        f"([dim]{len(list(_iter_sites()))} sites[/dim])"
    )

    results: list[dict[str, Any]] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("checking…", total=len(list(_iter_sites())))
        for item in check_username(username, SITES, concurrency=concurrency):
            results.append(item)
            progress.advance(task)

    # Pretty table
    table = Table(title=f"Results • {username}")
    table.add_column("Site", style="bold")
    table.add_column("Status")
    table.add_column("URL", style="dim")

    found = 0
    for r in results:
        site = str(r.get("site", ""))
        ok = bool(r.get("exists", False))
        url = str(r.get("url", ""))
        status = "[green]FOUND[/green]" if ok else "[red]not found[/red]"
        if ok:
            found += 1
        table.add_row(site, status, url)

    console.print(table)
    console.print(f"[bold]Found:[/bold] {found}/{len(results)}")

    if json_out:
        payload = {
            "username": username,
            "found": found,
            "total": len(results),
            "results": results,
        }
        json_out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        console.print(f"[dim]Saved →[/dim] [bold]{json_out}[/bold]")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
