import csv
from main import StandingsCalculator
from tests import test_unit_load_matches, test_unit_team_stats


def run_pipeline(input_file: str, output_file: str):
    calculator = StandingsCalculator()
    report = calculator.load_matches(input_file)
    league_table = calculator.calculate_standings(report.matches)
    calculator.save_standings_to_csv(league_table, output_file)
    return league_table

def test_end_to_end_known_league(tmp_path):
    inp = tmp_path / "input.csv"
    inp.write_text(
        "Home,Away,HS,AS\n"
        "Arsenal,Chelsea,2,1\n"
        "Liverpool,Manchester City,3,3\n"
        "Chelsea,Liverpool,0,2\n"
    )
    out = tmp_path / "output.csv"
    league_table = run_pipeline(inp, out)

    rows = list(csv.reader(out.read_text().splitlines()))
    header, body = rows[0], rows[1:]
    assert header[0] == "Team"
    names = [row[0] for row in body]
    assert names[0] in {"Liverpool", "Arsenal"}
    assert "Chelsea" not in names[:2]  # Chelsea should be lowered in the table

def test_output_file_roundtrips(tmp_path):
    inp = tmp_path / "input.csv"
    inp.write_text("A,B,5,3\n")
    out = tmp_path / "output.csv"
    run_pipeline(inp, out)

    text = out.read_text()
    assert text.endswith("\n")
    rows = list(csv.reader(text.splitlines()))
    assert len(rows[1]) == 9

def test_infinite_goal_average(tmp_path):
    inp = tmp_path / "input.csv"
    inp.write_text("Iron,Weak,5,0\n")
    out = tmp_path / "output.csv"
    run_pipeline(inp, out)

    rows = list(csv.reader(out.read_text().splitlines()))[1]
    assert rows[7] == 'inf'  # Goal Average column should be 'inf' for Iron

def test_empty_input_file(tmp_path):
    inp = tmp_path / "input.csv"
    inp.write_text("")  # Empty file
    out = tmp_path / "output.csv"
    run_pipeline(inp, out)

    rows = list(csv.reader(out.read_text().splitlines()))
    assert len(rows) == 1  # Only header row should be present