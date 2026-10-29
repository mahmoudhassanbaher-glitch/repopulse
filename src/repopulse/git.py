"""Thin wrapper around the ``git`` executable plus a parser for ``git log --numstat``."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Set, Tuple


class GitError(RuntimeError):
    """Raised when git is missing or a git command fails."""


@dataclass(frozen=True)
class FileChange:
    path: str
    added: int
    deleted: int


@dataclass(frozen=True)
class Commit:
    sha: str
    author: str
    email: str
    date: datetime
    subject: str
    files: Tuple[FileChange, ...] = ()


_FIELD_SEP = "\x1f"
_COMMIT_MARK = "@@@"
_LOG_FORMAT = f"{_COMMIT_MARK}%H%x1f%an%x1f%ae%x1f%aI%x1f%s"
_BRACE_RENAME = re.compile(r"\{(.*?) => (.*?)\}")


def normalize_path(raw: str) -> str:
    """Resolve numstat rename notation (``src/{old => new}/f.py``) to the new path."""
    if " => " not in raw:
        return raw
    if "{" in raw:
        resolved = _BRACE_RENAME.sub(lambda m: m.group(2), raw)
        return resolved.replace("//", "/").lstrip("/")
    return raw.split(" => ")[-1]


def parse_log(output: str) -> List[Commit]:
    """Parse the output of ``git log --numstat`` using :data:`_LOG_FORMAT`."""
    commits: List[Commit] = []
    header: Optional[List[str]] = None
    files: List[FileChange] = []

    def flush() -> None:
        if header is None:
            return
        sha, name, email, date, subject = header
        commits.append(
            Commit(sha, name, email, datetime.fromisoformat(date), subject, tuple(files))
        )

    for line in output.splitlines():
        if line.startswith(_COMMIT_MARK):
            flush()
            files = []
            header = line[len(_COMMIT_MARK):].split(_FIELD_SEP, 4)
            if len(header) != 5:
                raise GitError(f"unexpected log line: {line!r}")
        elif line.strip() and header is not None:
            parts = line.split("\t", 2)
            if len(parts) != 3:
                continue
            added, deleted, path = parts
            # Binary files are reported as "-"; count them as zero changed lines.
            files.append(
                FileChange(
                    normalize_path(path),
                    int(added) if added.isdigit() else 0,
                    int(deleted) if deleted.isdigit() else 0,
                )
            )
    flush()
    return commits


def _run(repo: Path, *args: str) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError as exc:
        raise GitError("git executable not found on PATH") from exc


def load_commits(
    repo: Path,
    since: Optional[str] = None,
    until: Optional[str] = None,
    author: Optional[str] = None,
) -> List[Commit]:
    """Load non-merge commits (newest first) with per-file line statistics."""
    check = _run(repo, "rev-parse", "--is-inside-work-tree")
    if check.returncode != 0:
        raise GitError(f"not a git repository: {repo}")

    cmd = ["log", "--no-merges", "--numstat", f"--pretty=format:{_LOG_FORMAT}"]
    if since:
        cmd.append(f"--since={since}")
    if until:
        cmd.append(f"--until={until}")
    if author:
        cmd.append(f"--author={author}")

    proc = _run(repo, *cmd)
    if proc.returncode != 0:
        if "does not have any commits" in proc.stderr:
            return []
        raise GitError(proc.stderr.strip() or "git log failed")
    return parse_log(proc.stdout)


def tracked_files(repo: Path) -> Set[str]:
    """Return the set of files that exist at HEAD."""
    proc = _run(repo, "ls-files")
    if proc.returncode != 0:
        raise GitError(proc.stderr.strip() or "git ls-files failed")
    return {line for line in proc.stdout.splitlines() if line}
