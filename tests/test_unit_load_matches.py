import os
import pytest
from main import StandingsCalculator

@pytest.fixture
def calculator():
    return StandingsCalculator()

def test_skips_header(calculator, tmp_path):
    f = tmp_path / "in.csv"
    f.write_text("Home,Away,HS,AS\nA,B,2,1\n")
    matches = calculator.load_matches(str(f))
    assert len(matches) == 1
    assert matches[0].home_team == "A"
    #assert matches[0].away_team == "B"
    #assert matches[0].home_team_score == 2
    #assert matches[0].away_team_score == 1

def test_four_column_no_week(calculator, tmp_path):
    f = tmp_path / "in.csv"
    f.write_text("A,B,2,1\n")
    matches = calculator.load_matches(str(f))
    assert matches[0].match_week is None

def test_five_column_with_week(calculator, tmp_path):
    f = tmp_path / "in.csv"
    f.write_text("1,A,B,2,1\n")
    matches = calculator.load_matches(str(f))
    assert matches[0].match_week == 1

def test_malformed_rows_are_skipped(calculator, tmp_path):
    f = tmp_path / "in.csv"
    f.write_text("1,A,B,2,1\nmalformed,row\n2,C,D,3,0\n")
    matches = calculator.load_matches(str(f))
    assert [m.home_team for m in matches] == ["A", "C"]

def test_blank_lines_are_skipped(calculator, tmp_path):
    f = tmp_path / "in.csv"
    f.write_text("\n\nA,B,1,0\n\n")
    assert len(calculator.load_matches(str(f))) == 1
