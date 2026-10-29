"""Plain-text rendering with optional ANSI colors."""

from __future__ import annotations

import math
import os
from typing import Any, Dict, Iterable, List, Sequence

_CODES = {"bold": "1", "green": "32", "yellow": "33", "red": "31", "cyan": "36"}
_SHADES = " ░▒▓█"


def use_color(stream) -> bool:
    return hasattr(stream, "isatty") and stream.isatty() and "NO_COLOR" not in os.environ


def style(text: str, name: str, enabled: bool) -> str:
    return f"\033[{_CODES[name]}m{text}\033[0m" if enabled else text


def table(headers: Sequence[str], rows: Iterable[Sequence[Any]], right: Sequence[int] = ()) -> str:
    rows = [[str(c) for c in r] for r in rows]
    widths = [max([len(h)] + [len(r[i]) for r in rows]) for i, h in enumerate(headers)]

    def fmt(cells: Sequence[str]) -> str:
        out = [c.rjust(widths[i]) if i in right else c.ljust(widths[i]) for i, c in enumerate(cells)]
        return "  ".join(out).rstrip()

    lines = [fmt(headers), "  ".join("-" * w for w in widths)]
    lines += [fmt(r) for r in rows]
    return "\n".join(lines)


def render_summary(data: Dict[str, Any], color: bool) -> str:
    out: List[str] = [style("Repository summary", "bold", color), ""]
    out.append(f"Commits        {data['commits']}")
    out.append(f"Active days    {data['active_days']}")
    out.append(f"Period         {data['first_commit'][:10]} → {data['last_commit'][:10]}")
    out.append(
        f"Lines          {style('+' + str(data['lines_added']), 'green', color)} "
        f"{style('-' + str(data['lines_deleted']), 'red', color)}"
    )
    out += ["", style("Top authors", "bold", color)]
    out.append(
        table(["Author", "Commits"], [(a["name"], a["commits"]) for a in data["authors"][:5]], right=[1])
    )
    out += ["", style("Most changed file types", "bold", color)]
    out.append(
        table(["Type", "Changes"], [(e["ext"], e["changes"]) for e in data["top_extensions"]], right=[1])
    )
    return "\n".join(out)


def render_hotspots(rows: List[Dict[str, Any]], color: bool) -> str:
    title = style("Hotspots (most frequently changed files)", "bold", color)
    body = table(
        ["File", "Commits", "Churn", "Authors"],
        [(r["path"], r["commits"], r["churn"], r["authors"]) for r in rows],
        right=[1, 2, 3],
    )
    return f"{title}\n\n{body}"


def render_bus_factor(data: Dict[str, Any], top: int, color: bool) -> str:
    tf = data["truck_factor"]
    tone = "red" if tf <= 1 else "yellow" if tf == 2 else "green"
    out = [
        style("Bus factor", "bold", color),
        "",
        f"Truck factor   {style(str(tf), tone, color)}  "
        f"(authors whose departure would orphan >50% of {data['files_analyzed']} files)",
        "",
        style("File ownership", "bold", color),
        table(
            ["Author", "Files", "Share"],
            [(o["author"], o["files"], f"{o['share']:.0%}") for o in data["owners"][:top]],
            right=[1, 2],
        ),
    ]
    if data["at_risk"]:
        out += ["", style("At-risk files (single dominant author)", "bold", color)]
        out.append(
            table(
                ["File", "Owner", "Share", "Commits"],
                [
                    (r["path"], r["owner"], f"{r['share']:.0%}", r["commits"])
                    for r in data["at_risk"][:top]
                ],
                right=[2, 3],
            )
        )
    return "\n".join(out)


def render_heatmap(data: Dict[str, Any], color: bool) -> str:
    matrix = data["matrix"]
    peak = max(max(row) for row in matrix) or 1
    header = "     " + "".join(f"{h:02d} " if h % 3 == 0 else "   " for h in range(24))
    lines = [style("Commit heatmap (author-local time)", "bold", color), "", header.rstrip()]
    for day, row in zip(data["weekdays"], matrix):
        cells = ""
        for v in row:
            level = 0 if v == 0 else math.ceil(v / peak * 4)
            cells += style(_SHADES[level] * 2, "cyan", color and level > 0) + " "
        lines.append(f"{day}  {cells}".rstrip())
    b = data["busiest"]
    lines += ["", f"Busiest slot: {b['weekday']} {b['hour']:02d}:00 ({b['commits']} commits)"]
    return "\n".join(lines)
