# usergator 🕵

A **legal OSINT username footprint checker**. Give it a username; it checks a curated list of public profile URL patterns and reports what appears to exist.

## Features (v0.1)
- Fast checks against a curated site list (no login, no scraping behind auth)
- Outputs results to terminal + optional JSON export
- Safe defaults (rate-limited, user-agent set)

## Install (dev)
```bash
git clone https://github.com/vireline/usergator
cd usergator

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
pip install -e .

# smoke tests
usergator --help
usergator sites
usergator check octocat
usergator check octocat --json out.json && cat out.json | head

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
