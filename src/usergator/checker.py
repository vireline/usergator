from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Optional

import httpx

@dataclass
class CheckResult:
    site: str
    url: str
    exists: bool
    status_code: Optional[int] = None
    error: Optional[str] = None

async def _check_one(client: httpx.AsyncClient, site: str, url: str) -> CheckResult:
    try:
        r = await client.get(url, follow_redirects=True, timeout=10.0)
        # Heuristic: 2xx/3xx likely exists; 404 likely doesn't.
        exists = (200 <= r.status_code < 400) and (r.status_code != 404)
        if r.status_code == 404:
            exists = False
        return CheckResult(site=site, url=str(r.url), exists=exists, status_code=r.status_code)
    except Exception as e:
        return CheckResult(site=site, url=url, exists=False, error=str(e))

async def check_username(username: str, site_patterns: dict[str, str], concurrency: int = 8) -> list[CheckResult]:
    headers = {"User-Agent": "usergator/0.1 (respectful OSINT checker)"}
    limits = httpx.Limits(max_connections=concurrency, max_keepalive_connections=concurrency)
    async with httpx.AsyncClient(headers=headers, limits=limits) as client:
        sem = asyncio.Semaphore(concurrency)

        async def guarded(site: str, url: str):
            async with sem:
                return await _check_one(client, site, url)

        tasks = []
        for site, pattern in site_patterns.items():
            url = pattern.format(u=username)
            tasks.append(guarded(site, url))

        return await asyncio.gather(*tasks)
