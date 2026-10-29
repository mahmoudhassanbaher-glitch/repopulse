"""Command-line interface."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from . import __version__, analysis, render
from .git import GitError, load_commits, tracked_files


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("path", nargs="?", default=".", help="git repository (default: current dir)")
    common.add_argument("--since", help='only commits after this date, e.g. "2024-01-01" or "6 months ago"')
    common.add_argument("--until", help="only commits before this date")
    common.add_argument("--author", help="only commits by authors matching this pattern")
    common.add_argument("--json", action="store_true", dest="as_json", help="machine-readable output")

    parser = argparse.ArgumentParser(
        prog="repopulse", description="Analyze the pulse of a git repository."
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("summary", parents=[common], help="overview: commits, authors, file types")

    p = sub.add_parser("hotspots", parents=[common], help="most frequently changed files")
    p.add_argument("--top", type=int, default=10, help="number of files to show (default: 10)")

    p = sub.add_parser("busfactor", parents=[common], help="estimate the truck factor and risky files")
    p.add_argument("--top", type=int, default=10, help="rows per table (default: 10)")
    p.add_argument("--threshold", type=float, default=0.8, help="ownership share that counts as dominant")

    sub.add_parser("heatmap", parents=[common], help="commits by weekday and hour")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    repo = Path(args.path)
    try:
        commits = load_commits(repo, since=args.since, until=args.until, author=args.author)
        if not commits:
            print("No commits found for the given filters.", file=sys.stderr)
            return 1

        color = render.use_color(sys.stdout) and not args.as_json
        if args.command == "summary":
            data = analysis.summary(commits)
            text = render.render_summary(data, color)
        elif args.command == "hotspots":
            data = analysis.hotspots(commits, top=args.top)
            text = render.render_hotspots(data, color)
        elif args.command == "busfactor":
            data = analysis.bus_factor(
                commits, dominance=args.threshold, existing=tracked_files(repo)
            )
            text = render.render_bus_factor(data, args.top, color)
        else:
            data = analysis.heatmap(commits)
            text = render.render_heatmap(data, color)
    except GitError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(data, indent=2) if args.as_json else text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
