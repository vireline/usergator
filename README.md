# usergator 🕵️‍♀️

A **legal OSINT username footprint checker**. Give it a username; it checks a curated list of public profile URL patterns and reports what appears to exist.

## Features (v0.1)
- Fast checks against a curated site list (no login, no scraping behind auth)
- Outputs results to terminal + optional JSON export
- Safe defaults (rate-limited, user-agent set)

## Install (dev)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -U pip
pip install -e .
```

## Usage
```bash
usergator check <username>
usergator check <username> --json out.json
usergator sites
```

## Notes
This tool only checks **public** endpoints. Respect ToS and local laws.
