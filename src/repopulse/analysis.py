"""Pure functions that turn a list of commits into statistics (no I/O, easy to test)."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import PurePosixPath
from typing import Any, Dict, Iterable, List, Optional, Set

from .git import Commit

WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def summary(commits: List[Commit]) -> Dict[str, Any]:
    authors = Counter(c.author for c in commits)
    extensions: Counter = Counter()
    added = deleted = 0
    for c in commits:
        for f in c.files:
            added += f.added
            deleted += f.deleted
            extensions[PurePosixPath(f.path).suffix or "(none)"] += 1
    dates = [c.date for c in commits]
    return {
        "commits": len(commits),
        "authors": [{"name": n, "commits": k} for n, k in authors.most_common()],
        "first_commit": min(dates).isoformat() if dates else None,
        "last_commit": max(dates).isoformat() if dates else None,
        "active_days": len({d.date() for d in dates}),
        "lines_added": added,
        "lines_deleted": deleted,
        "top_extensions": [{"ext": e, "changes": n} for e, n in extensions.most_common(5)],
    }


def hotspots(commits: List[Commit], top: int = 10) -> List[Dict[str, Any]]:
    """Files that change most often: frequent change + high churn = likely trouble."""
    count: Counter = Counter()
    churn: Counter = Counter()
    authors: Dict[str, Set[str]] = defaultdict(set)
    for c in commits:
        for f in c.files:
            count[f.path] += 1
            churn[f.path] += f.added + f.deleted
            authors[f.path].add(c.author)
    ranked = sorted(count, key=lambda p: (-count[p], -churn[p], p))[:top]
    return [
        {"path": p, "commits": count[p], "churn": churn[p], "authors": len(authors[p])}
        for p in ranked
    ]


def bus_factor(
    commits: List[Commit],
    dominance: float = 0.8,
    min_commits: int = 3,
    existing: Optional[Iterable[str]] = None,
) -> Dict[str, Any]:
    """Estimate the truck factor.

    The owner of a file is the author with the most changed lines in it. The truck factor
    is the smallest number of authors whose departure would orphan more than half of all
    files (greedy, largest owners first). Files dominated by a single author and touched
    at least ``min_commits`` times are reported as at-risk.
    """
    alive = set(existing) if existing is not None else None
    churn: Dict[str, Counter] = defaultdict(Counter)
    touches: Counter = Counter()
    for c in commits:
        for f in c.files:
            if alive is not None and f.path not in alive:
                continue
            churn[f.path][c.author] += f.added + f.deleted
            touches[f.path] += 1

    owners: Dict[str, str] = {}
    at_risk: List[Dict[str, Any]] = []
    for path, by_author in churn.items():
        total = sum(by_author.values())
        if total == 0:
            continue  # binary or empty changes carry no ownership signal
        owner, lines = max(by_author.items(), key=lambda kv: (kv[1], kv[0]))
        owners[path] = owner
        share = lines / total
        if share >= dominance and touches[path] >= min_commits:
            at_risk.append(
                {"path": path, "owner": owner, "share": round(share, 3), "commits": touches[path]}
            )
    at_risk.sort(key=lambda r: (-r["commits"], -r["share"], r["path"]))

    total_files = len(owners)
    owned = Counter(owners.values())
    orphaned = truck = 0
    for _, n in owned.most_common():
        orphaned += n
        truck += 1
        if orphaned * 2 > total_files:
            break

    return {
        "truck_factor": truck,
        "files_analyzed": total_files,
        "owners": [
            {"author": a, "files": n, "share": round(n / total_files, 3)}
            for a, n in owned.most_common()
        ],
        "at_risk": at_risk,
    }


def heatmap(commits: List[Commit]) -> Dict[str, Any]:
    """Commit counts by weekday (Mon-Sun) and hour, in each author's local time."""
    matrix = [[0] * 24 for _ in range(7)]
    for c in commits:
        matrix[c.date.weekday()][c.date.hour] += 1
    best = max(((d, h) for d in range(7) for h in range(24)), key=lambda dh: matrix[dh[0]][dh[1]])
    return {
        "weekdays": WEEKDAYS,
        "matrix": matrix,
        "total": len(commits),
        "busiest": {
            "weekday": WEEKDAYS[best[0]],
            "hour": best[1],
            "commits": matrix[best[0]][best[1]],
        },
    }
