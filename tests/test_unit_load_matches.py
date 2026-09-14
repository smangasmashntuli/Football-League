import pytest
from main import StandingsCalculator


@pytest.fixture
def calculator():
    return StandingsCalculator()


def test_skips_header(calculator, tmp_path):
    f = tmp_path / "in.csv"
    f.write_text("Home,Away,HS,AS\nArsenal,Liverpool,2,1\n")
    report = calculator.load_matches(str(f))
    assert [m.home_team for m in report.matches] == ["Arsenal"]
    assert report.schema == "4-column"


def test_four_column_no_week(calculator, tmp_path):
    f = tmp_path / "in.csv"
    f.write_text("A,B,2,1\n")
    report = calculator.load_matches(str(f))
    assert report.matches[0].match_week is None


def test_five_column_with_week(calculator, tmp_path):
    f = tmp_path / "in.csv"
    f.write_text("1,A,B,2,1\n")
    report = calculator.load_matches(str(f))
    assert report.matches[0].match_week == 1
    assert report.schema == "5-column"


def test_blank_lines_are_skipped(calculator, tmp_path):
    f = tmp_path / "in.csv"
    f.write_text("\n\nA,B,1,0\n\n")
    assert len(calculator.load_matches(str(f)).matches) == 1


def test_malformed_row_is_reported_not_silent(calculator, tmp_path):
    f = tmp_path / "in.csv"
    f.write_text("1,Arsenal,Burnley,2,1\nmalformed,row\n2,Chelsea,Derby County,3,0\n")
    report = calculator.load_matches(str(f))
    assert [m.home_team for m in report.matches] == ["Arsenal", "Chelsea"]
    assert len(report.errors) == 1
    assert report.errors[0].line == 2
    assert "expected 5 columns" in report.errors[0].reason


def test_schema_is_enforced_per_file(calculator, tmp_path):
    f = tmp_path / "in.csv"
    f.write_text("1,A,B,2,1\nC,D,1,0\n")  # 5-col then a 4-col row
    report = calculator.load_matches(str(f))
    assert len(report.matches) == 1
    assert len(report.errors) == 1
    assert "expected 5 columns" in report.errors[0].reason


def test_non_numeric_score_is_reported(calculator, tmp_path):
    f = tmp_path / "in.csv"
    f.write_text("1,Arsenal,Burnley,2,1\n2,Chelsea,Derby County,abc,0\n")
    report = calculator.load_matches(str(f))
    assert len(report.matches) == 1
    assert report.errors[0].line == 2
    assert "must be integers" in report.errors[0].reason


def test_negative_score_is_rejected(calculator, tmp_path):
    f = tmp_path / "in.csv"
    f.write_text("1,Arsenal,Burnley,2,1\n2,Chelsea,Derby County,-1,0\n")
    report = calculator.load_matches(str(f))
    assert "non-negative" in report.errors[0].reason


def test_invalid_match_week_is_rejected(calculator, tmp_path):
    f = tmp_path / "in.csv"
    f.write_text("round one,A,B,1,0\n")
    report = calculator.load_matches(str(f))
    assert len(report.matches) == 0
    assert "match week must be an integer" in report.errors[0].reason


def test_malformed_first_row_is_an_error(calculator, tmp_path):
    f = tmp_path / "in.csv"
    f.write_text("garbage,stuff\nA,B,1,0\n")
    report = calculator.load_matches(str(f))
    assert any("cannot detect schema" in e.reason for e in report.errors)
    assert len(report.matches) == 1  # later rows still load in lenient mode


def test_strict_mode_raises_on_any_problem(calculator, tmp_path):
    f = tmp_path / "in.csv"
    f.write_text("1,A,B,2,1\n2,C,D,x,0\n")
    with pytest.raises(ValueError, match="invalid fixtures input"):
        calculator.load_matches(str(f), strict=True)


def test_unknown_team_reported_and_tallied(calculator, tmp_path):
    f = tmp_path / "in.csv"
    f.write_text("1,Random FC,B,2,0\n")
    report = calculator.load_matches(str(f))
    assert report.unknown_teams == ["Random FC", "B"]
    assert len(report.matches) == 1
    assert report.matches[0].home_team == "random fc"  # normalized fallback


def test_name_variants_normalized(calculator, tmp_path):
    f = tmp_path / "in.csv"
    f.write_text("1,Derby Country,Burnely,2,1\n2,WestHam,Carslie,0,0\n")
    report = calculator.load_matches(str(f))
    assert report.unknown_teams == []
    home_teams = {m.home_team for m in report.matches}
    away_teams = {m.away_team for m in report.matches}
    assert home_teams == {"Derby County", "West Ham United"}
    assert away_teams == {"Burnley", "Carlisle United"}


def test_strict_raises_on_unknown_team(calculator, tmp_path):
    f = tmp_path / "in.csv"
    f.write_text("1,AC Milan,B,2,0\n")
    with pytest.raises(ValueError, match="AC Milan"):
        calculator.load_matches(str(f), strict=True)
