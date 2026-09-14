from main import Match, LeagueTable

def make_table(*matches):
    t = LeagueTable()
    for i in matches:
        t.process_match(i)
    return t

def test_sort_teams():
    t = make_table(
        Match("A", "X", 5, 1),
        Match("B", "Y", 3, 1),
        Match("C", "T", 1, 1),
        Match("D", "X", 1, 1),
        Match("E", "Y", 1, 1),
    )

    order = [s.team_name for s in t.get_table()]
    assert order.index("A") < order.index("B") < order.index("C")
    assert order.index("Y") < order.index("X")

def test_to_csv_header_column():
    t = make_table(Match("A", "B", 1, 5))
    lines = t.to_csv().splitlines()
    assert lines[0] == "Team,Played,Won,Drawn,Lost,Goals Scored,Goals Conceded,Goal Average,Points"
    assert all(len(l.split(",")) == 9 for l in lines)