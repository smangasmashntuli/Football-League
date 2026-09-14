import math
import pytest
from main import TeamStats

class TestGoalAverage:
    def test_normal_ratio(self):
        t = TeamStats("A", goals_scored=10, goals_conceded=2)
        assert t.goal_average() == 5.0

    def test_zero_conceded_returns_inf(self):
        t = TeamStats("A", goals_scored=5, goals_conceded=0)
        assert math.isinf(t.goal_average())

    def test_zero_scored_zero_conceded_is_inf(self):
        t = TeamStats("A", goals_scored=0, goals_conceded=0)
        assert math.isinf(t.goal_average())


class TestAddLoss:
    def test_loss_does_not_reset_points(self):
        t = TeamStats("A")
        t.add_win(2, 1)
        t.add_draw(1, 1)
        t.add_loss(0, 3)
        assert t.points == 3  # 2 for win + 1 for draw +
        assert (t.played, t.won, t.drawn, t.lost) == (3, 1, 1, 1)
        assert (t.goals_scored, t.goals_conceded) == (3, 5)

    def test_loss_records_goals(self):
        t = TeamStats("A")
        t.add_loss(1, 4)
        assert t.goals_scored == 1
        assert t.goals_conceded == 4
