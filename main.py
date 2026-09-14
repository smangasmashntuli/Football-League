import csv
import os
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class Match:
    home_team: str
    away_team: str
    home_team_score: int
    away_team_score: int
    match_week: int | None = None

    def is_draw(self) -> bool:
        return self.home_team_score == self.away_team_score

    def winner(self) -> str | None:
        if self.is_draw():
            return None
        return self.home_team if self.home_team_score > self.away_team_score else self.away_team

    def loser(self) -> str | None:
        if self.is_draw():
            return None
        return self.home_team if self.home_team_score < self.away_team_score else self.away_team


@dataclass
class TeamStats:
    team_name: str
    played: int = 0
    won: int = 0
    drawn: int = 0
    lost: int = 0
    goals_scored: int = 0
    goals_conceded: int = 0
    points: int = 0

    def goal_average(self) -> float:
        if self.goals_conceded == 0:
            return float('inf')  # Never conceded, so the ratio is unbounded
        return self.goals_scored / self.goals_conceded

    def add_win(self, goals_scored: int, goals_conceded: int) -> None:
        self.played += 1
        self.won += 1
        self.goals_scored += goals_scored
        self.goals_conceded += goals_conceded
        self.points += 2

    def add_draw(self, goals_scored: int, goals_conceded: int) -> None:
        self.played += 1
        self.drawn += 1
        self.goals_scored += goals_scored
        self.goals_conceded += goals_conceded
        self.points += 1

    def add_loss(self, goals_scored: int, goals_conceded: int) -> None:
        self.played += 1
        self.lost += 1
        self.goals_scored += goals_scored
        self.goals_conceded += goals_conceded
        self.points += 0


class LeagueTable:
    def __init__(self):
        self.teams: Dict[str, TeamStats] = {}

    def _get_or_create_team(self, team_name: str) -> TeamStats:
        if team_name not in self.teams:
            self.teams[team_name] = TeamStats(team_name)
        return self.teams[team_name]

    def process_match(self, match: Match) -> None:
        home_team_stats = self._get_or_create_team(match.home_team)
        away_team_stats = self._get_or_create_team(match.away_team)

        if match.is_draw():
            home_team_stats.add_draw(match.home_team_score, match.away_team_score)
            away_team_stats.add_draw(match.away_team_score, match.home_team_score)
        else:
            winner = match.winner()
            loser = match.loser()
            if winner == match.home_team:
                home_team_stats.add_win(match.home_team_score, match.away_team_score)
                away_team_stats.add_loss(match.away_team_score, match.home_team_score)
            else:
                away_team_stats.add_win(match.away_team_score, match.home_team_score)
                home_team_stats.add_loss(match.home_team_score, match.away_team_score)

        return

    def get_table(self) -> List[TeamStats]:
        return sorted(self.teams.values(), key=lambda x: (-x.points, -x.goal_average(), -x.goals_scored, x.team_name))

    def to_csv(self) -> str:
        header = "Team,Played,Won,Drawn,Lost,Goals Scored,Goals Conceded,Goal Average,Points"
        rows = [header]
        for team_stats in self.get_table():
            row = (
                f"{team_stats.team_name},{team_stats.played},{team_stats.won},"
                f"{team_stats.drawn},{team_stats.lost},{team_stats.goals_scored},"
                f"{team_stats.goals_conceded},{team_stats.goal_average()},{team_stats.points}"
            )
            rows.append(row)
        return "\n".join(rows)

class StandingsCalculator:
    def load_matches(self, filepath: str) -> List[Match]:
        matches: List[Match] = []
        with open(filepath, 'r', newline='') as file:
            reader = csv.reader(file)
            for row in reader:
                if not row:
                    continue  # skip blank lines
                if len(row) == 5:
                    match_week = row[0].strip()
                elif len(row) == 4:
                    match_week = None  # Backwards-compatible: no Match Week column
                else:
                    continue  # skip the header row and malformed rows
                home_team, away_team, home_score, away_score = (c.strip() for c in row[-4:])
                if not home_team or not away_team:
                    continue  # skip rows with empty team names
                try:
                    hs = int(home_score)
                    as_ = int(away_score)
                    mw = int(match_week) if match_week else None
                except ValueError:
                    continue  # skip the header row (non-numeric scores) and malformed rows
                matches.append(Match(home_team, away_team, hs, as_, mw))
        return matches

    def calculate_standings(self, matches: List[Match]) -> LeagueTable:
        league_table = LeagueTable()
        for match in matches:
            league_table.process_match(match)
        return league_table

    def save_standings_to_csv(self, league_table: LeagueTable, filepath: str) -> None:
        parent = os.path.dirname(filepath)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(filepath, 'w', newline='') as file:
            file.write(league_table.to_csv())
            file.write('\n')


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(base_dir, 'data','input.csv')
    output_file = os.path.join(base_dir, 'data', 'output.csv')

    calculator = StandingsCalculator()
    matches = calculator.load_matches(input_file)
    league_table = calculator.calculate_standings(matches)
    calculator.save_standings_to_csv(league_table, output_file)
    print(league_table.to_csv())


if __name__ == "__main__":
    main()
