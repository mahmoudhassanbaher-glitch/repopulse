import os
import subprocess

import pytest


@pytest.fixture()
def repo(tmp_path):
    """A small throw-away repo: alice owns a.py, bob owns b.py, both touch README.md."""

    def git(*args, author=("Alice", "alice@example.com"), date="2024-01-01T10:00:00+00:00"):
        env = {
            **os.environ,
            "GIT_AUTHOR_NAME": author[0],
            "GIT_AUTHOR_EMAIL": author[1],
            "GIT_COMMITTER_NAME": author[0],
            "GIT_COMMITTER_EMAIL": author[1],
            "GIT_AUTHOR_DATE": date,
            "GIT_COMMITTER_DATE": date,
        }
        subprocess.run(
            ["git", "-C", str(tmp_path), "-c", "commit.gpgsign=false", *args],
            check=True,
            capture_output=True,
            env=env,
        )

    def commit(name, content, who, date, message):
        (tmp_path / name).write_text(content)
        git("add", name, author=who, date=date)
        git("commit", "-m", message, author=who, date=date)

    alice, bob = ("Alice", "alice@example.com"), ("Bob", "bob@example.com")
    git("init", "-q")
    commit("a.py", "print(1)\n", alice, "2024-01-01T10:00:00+00:00", "add a")  # Mon 10h
    commit("a.py", "print(1)\nprint(2)\n", alice, "2024-01-02T10:30:00+00:00", "extend a")  # Tue
    commit("a.py", "print(1)\nprint(2)\nprint(3)\n", alice, "2024-01-03T22:00:00+00:00", "more a")
    commit("b.py", "x = 1\n", bob, "2024-01-04T09:00:00+00:00", "add b")  # Thu 9h
    commit("README.md", "# demo\n", alice, "2024-01-05T09:15:00+00:00", "readme")  # Fri
    return tmp_path
