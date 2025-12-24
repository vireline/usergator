from __future__ import annotations

import asyncio
import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

from .checker import check_username
from .sites import SITES

app = typer.Typer(add_completion=False, help="OSINT username footprint investigator")
console = Console()


def _result_to_dict(r: Any) -> dict[str, Any]:
    """Normalize CheckResult/dataclass/obj/dict into a plain dict."""
    if isinstance(r, dict):
        return r
    if is_dataclass(r):
        return asdict(r)
    return {
        "site": getattr(r, "site", None),
        "url": getattr(r, "url", None),
        "exists": getattr(r, "exists", None),
        "status_code": getattr(r, "status_code", None),
        "error": getattr(r, "error", None),
    }


@app.command()
def sites() -> None:
    """List the built-in site patterns."""
    table = Table(
        title="usergator • Username Sources",
        header_style="bold cyan",
        border_style="cyan",
        show_lines=False,
    )
    table.add_column("Site", style="bold")
    table.add_column("Pattern", style="dim")

    # SITES is a dict[str, str]
    for name, pattern in SITES.items():
        table.add_row(str(name), str(pattern))

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
        Panel.fit(
            f"[bold cyan]usergator[/bold cyan] • scanning [bold]{username}[/bold]\n"
            f"[dim]{len(SITES)} sites • concurrency={concurrency}[/dim]",
            border_style="cyan",
        )
    )

    async def _run() -> Any:
        # check_username is async and returns a list of CheckResult (or dict-like)
        return await check_username(username, SITES, concurrency=concurrency)

    with Progress(
        SpinnerColumn(style="cyan"),
        TextColumn("[bold]{task.description}[/bold]"),
        BarColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("checking…", total=len(SITES))
        items = asyncio.run(_run())
        progress.update(task, completed=len(SITES))

    out = [_result_to_dict(x) for x in (items or [])]

    table = Table(
        title=f"Results • {username}",
        header_style="bold cyan",
        border_style="cyan",
        show_lines=False,
    )
    table.add_column("Site", style="bold")
    table.add_column("Status", justify="center")
    table.add_column("HTTP", justify="right", style="dim")
    table.add_column("URL", overflow="fold")

    found = 0
    for d in out:
        ok = bool(d.get("exists"))
        code = d.get("status_code")
        err = d.get("error")

        if err:
            status = "[yellow]error[/yellow]"
        else:
            status = "[green]FOUND[/green]" if ok else "[red]not found[/red]"

        if ok:
            found += 1

        table.add_row(
            str(d.get("site") or ""),
            status,
            "" if code is None else str(code),
            str(d.get("url") or ""),
        )

    console.print(table)
    console.print(f"[bold]{found}[/bold] found out of [bold]{len(out)}[/bold].")

    if json_out:
        json_out.write_text(
            json.dumps(out, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        console.print(f"[dim]Saved →[/dim] [bold]{json_out}[/bold]")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
