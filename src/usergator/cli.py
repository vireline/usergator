cd ~/usergator

python3 - <<'PY'
from pathlib import Path

p = Path("src/usergator/cli.py")

code = r'''from __future__ import annotations

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
    Normalize SITES into (name, pattern/url) pairs.

    Supports:
    - dict: {"GitHub": "https://github.com/{u}", ...}
    - list/tuple of 2-tuples: [("GitHub","https://..."), ...]
    - list of dicts: [{"name":"GitHub","url":"..."}, {"site":"GitHub","pattern":"..."}]
    - list of strings: ["https://github.com/{u}", ...] (falls back to numbered names)
    """
    s = SITES

    if isinstance(s, dict):
        for k, v in s.items():
            yield str(k), str(v)
        return

    if isinstance(s, (list, tuple)):
        for i, item in enumerate(s, 1):
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                yield str(item[0]), str(item[1])
            elif isinstance(item, dict):
                name = item.get("name") or item.get("site") or f"Site {i}"
                pat = item.get("url") or item.get("pattern") or item.get("link") or ""
                yield str(name), str(pat)
            elif isinstance(item, str):
                yield f"Site {i}", item
            else:
                yield f"Site {i}", str(item)
        return

    # Unknown structure — last resort:
    yield "Sites", str(s)


def _sites_len() -> int:
    try:
        return len(SITES)  # type: ignore[arg-type]
    except Exception:
        return sum(1 for _ in _iter_sites())


@app.command()
def sites() -> None:
    """List the built-in site patterns."""
    table = Table(title="usergator • sources", header_style="bold magenta")
    table.add_column("Site", style="bold")
    table.add_column("Pattern", style="dim", overflow="fold")
    for name, pat in _iter_sites():
        table.add_row(name, pat)
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
    total = _sites_len()
    console.print(
        f"\n[bold cyan]usergator[/bold cyan]  scanning  [bold]{username}[/bold]  "
        f"([dim]{total} sites[/dim])\n"
    )

    results: list[dict[str, Any]] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("checking…", total=total)

        # IMPORTANT: checker expects site_patterns as a required positional arg
        for item in check_username(username, SITES, concurrency=concurrency):
            results.append(item)
            progress.advance(task)

    table = Table(header_style="bold magenta")
    table.add_column("Site", style="bold")
    table.add_column("URL", style="dim", overflow="fold")
    table.add_column("Status", justify="center")

    def fmt(status: str) -> str:
        s = (status or "").upper()
        if s == "FOUND":
            return "[bold green]FOUND[/bold green]"
        if s == "NOT_FOUND":
            return "[dim]NOT FOUND[/dim]"
        return "[yellow]UNKNOWN[/yellow]"

    found = not_found = unknown = 0
    for r in results:
        status = (r.get("status") or "UNKNOWN").upper()
        if status == "FOUND":
            found += 1
        elif status == "NOT_FOUND":
            not_found += 1
        else:
            unknown += 1

        table.add_row(str(r.get("site", "?")), str(r.get("url", "")), fmt(status))

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
'''
p.write_text(code, encoding="utf-8")
print("✅ Rewrote src/usergator/cli.py with robust SITES handling + correct check_username() call.")
PY
