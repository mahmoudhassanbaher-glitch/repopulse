# RepoPulse

[![CI](https://github.com/<your-username>/repopulse/actions/workflows/ci.yml/badge.svg)](https://github.com/<your-username>/repopulse/actions)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

A zero-dependency command-line tool that reads the history of any git repository and tells you
**where the risk is**: which files churn the most, how concentrated code ownership is
(the *bus factor*), and when the team actually works.

```text
$ repopulse busfactor

Bus factor

Truck factor   2  (authors whose departure would orphan >50% of 41 files)

File ownership
Author  Files  Share
------  -----  -----
Alice      19    46%
Bob        14    34%
Carol       8    20%

At-risk files (single dominant author)
File                 Owner  Share  Commits
-------------------  -----  -----  -------
src/billing/core.py  Alice   94%       23
```

## Why

Code review tells you whether a *change* is good. It does not tell you whether the *system*
is fragile. Files that are changed constantly and understood by only one person are where
outages and onboarding pain come from. RepoPulse surfaces them from data you already have.

## Install

```bash
pip install git+https://github.com/<your-username>/repopulse.git
# or, from a clone:
pip install -e .
```

Requires Python 3.9+ and `git` on your `PATH`. No third-party dependencies.

## Usage

```bash
repopulse summary   [PATH]              # commits, authors, file types
repopulse hotspots  [PATH] --top 15     # most frequently changed files
repopulse busfactor [PATH]              # truck factor + at-risk files
repopulse heatmap   [PATH]              # commits by weekday and hour
```

Every command accepts:

| Option            | Description                                              |
| ----------------- | -------------------------------------------------------- |
| `--since DATE`    | Only commits after a date, e.g. `2025-01-01`, `"6 months ago"` |
| `--until DATE`    | Only commits before a date                               |
| `--author PAT`    | Only commits by matching authors                         |
| `--json`          | Machine-readable output (pipe into `jq`, dashboards, CI) |

Exit codes: `0` ok, `1` no commits matched, `2` error (e.g. not a git repository).

## How it works

- **Parsing** – one `git log --numstat` call with a custom delimiter-based format; rename
  notation (`src/{old => new}/f.py`) and binary files are handled explicitly.
- **Ownership** – a file's owner is the author with the most changed lines in it. Only files
  that still exist at `HEAD` are counted, so deleted code doesn't skew results.
- **Truck factor** – the smallest number of authors whose departure would orphan more than
  half of all files (greedy, largest owners first). It is a heuristic, not a measurement;
  treat it as a conversation starter.
- **Design** – `git.py` (I/O) → `analysis.py` (pure functions) → `render.py` (presentation)
  → `cli.py` (wiring). The analysis layer has no I/O, which keeps it trivially testable.

## Development

```bash
pip install -e ".[dev]"
ruff check .
pytest
```

Tests build throw-away git repositories with fixed authors and dates, so they exercise the real
`git` integration instead of mocking it. CI runs on Python 3.9, 3.11 and 3.12.

## Roadmap

- [ ] Weight ownership by recency (blame-based, decaying contributions)
- [ ] `--format markdown` for pasting reports into pull requests
- [ ] Coupling analysis: files that always change together
- [ ] Publish to PyPI

## License

MIT
