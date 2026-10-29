import json

from repopulse.cli import main


def test_summary_text(repo, capsys):
    assert main(["summary", str(repo)]) == 0
    assert "Repository summary" in capsys.readouterr().out


def test_hotspots_json(repo, capsys):
    assert main(["hotspots", str(repo), "--json", "--top", "1"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data[0]["path"] == "a.py"


def test_busfactor_and_heatmap_render(repo, capsys):
    assert main(["busfactor", str(repo)]) == 0
    assert "Truck factor" in capsys.readouterr().out
    assert main(["heatmap", str(repo)]) == 0
    assert "Busiest slot" in capsys.readouterr().out


def test_not_a_repo_returns_error(tmp_path, capsys):
    assert main(["summary", str(tmp_path)]) == 2
    assert "not a git repository" in capsys.readouterr().err


def test_no_matching_commits(repo, capsys):
    assert main(["summary", str(repo), "--author", "nobody"]) == 1
