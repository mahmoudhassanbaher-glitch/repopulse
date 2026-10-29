from repopulse import analysis
from repopulse.git import load_commits, tracked_files


def test_summary(repo):
    s = analysis.summary(load_commits(repo))
    assert s["commits"] == 5
    assert s["authors"][0] == {"name": "Alice", "commits": 4}
    assert s["active_days"] == 5


def test_hotspots_rank_most_changed_first(repo):
    top = analysis.hotspots(load_commits(repo), top=2)
    assert top[0]["path"] == "a.py" and top[0]["commits"] == 3
    assert len(top) == 2


def test_bus_factor(repo):
    result = analysis.bus_factor(load_commits(repo), existing=tracked_files(repo))
    assert result["files_analyzed"] == 3
    assert result["truck_factor"] == 1  # Alice owns 2 of 3 files
    assert result["at_risk"][0]["path"] == "a.py"
    assert result["at_risk"][0]["owner"] == "Alice"


def test_bus_factor_ignores_deleted_files(repo):
    result = analysis.bus_factor(load_commits(repo), existing={"b.py"})
    assert result["files_analyzed"] == 1
    assert result["owners"][0]["author"] == "Bob"


def test_heatmap(repo):
    h = analysis.heatmap(load_commits(repo))
    assert sum(map(sum, h["matrix"])) == 5
    assert h["matrix"][0][10] == 1  # Monday 10:00
