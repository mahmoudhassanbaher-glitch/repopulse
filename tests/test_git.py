from repopulse.git import load_commits, normalize_path, parse_log

SAMPLE = (
    "@@@abc\x1fAlice\x1fa@x.io\x1f2024-03-04T10:00:00+01:00\x1ffix: thing\n"
    "3\t1\tsrc/app.py\n"
    "-\t-\tlogo.png\n"
    "\n"
    "@@@def\x1fBob\x1fb@x.io\x1f2024-03-03T08:30:00+00:00\x1frename\n"
    "0\t0\tsrc/{old => new}/mod.py\n"
)


def test_parse_log_reads_commits_and_files():
    commits = parse_log(SAMPLE)
    assert [c.sha for c in commits] == ["abc", "def"]
    assert commits[0].files[0].added == 3 and commits[0].files[0].deleted == 1
    assert commits[0].files[1].added == 0  # binary file
    assert commits[1].files[0].path == "src/new/mod.py"


def test_normalize_path_variants():
    assert normalize_path("plain.py") == "plain.py"
    assert normalize_path("old.py => new.py") == "new.py"
    assert normalize_path("sub/{old => }/f.py") == "sub/f.py"
    assert normalize_path("{ => sub}/f.py") == "sub/f.py"


def test_load_commits_from_real_repo(repo):
    commits = load_commits(repo)
    assert len(commits) == 5
    assert load_commits(repo, author="Bob")[0].author == "Bob"
