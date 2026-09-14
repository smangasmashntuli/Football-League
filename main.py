import argparse
import csv
import io
import os
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional

WIN_POINTS = 2
DRAW_POINTS = 1
LOSS_POINTS = 0

SEASON = "1974/75 English First Division"

TEAM_ALIASES: Dict[str, List[str]] = {
    "Arsenal": ["arsenal"],
    "Birmingham City": ["birmingham", "birmingham city", "brum"],
    "Burnley": ["burnley", "burnely", "burley"],
    "Carlisle United": ["carlisle", "carlisle united", "carslie"],
    "Chelsea": ["chelsea"],
    "Coventry City": ["coventry", "coventry city"],
    "Derby County": ["derby county", "derby country", "derby", "derby co"],
    "Everton": ["everton"],
    "Ipswich Town": ["ipswich", "ipswich town"],
    "Leeds United": ["leeds", "leeds united"],
    "Leicester City": ["leicester", "leicester city"],
    "Liverpool": ["liverpool"],
    "Luton Town": ["luton", "luton town"],
    "Manchester City": ["manchester city", "man city"],
    "Middlesbrough": ["middlesbrough", "middlesborough", "boro"],
    "Newcastle United": ["newcastle", "newcastle united"],
    "Queens Park Rangers": ["queens park rangers", "queen park rangers",
                            "queen park rovers", "queens park rovers",
                            "qpr", "q.p.r."],
    "Sheffield United": ["sheffield united"],
    "Stoke City": ["stoke", "stoke city"],
    "Tottenham Hotspur": ["tottenham", "tottenham hotspur", "spurs"],
    "West Ham United": ["west ham", "west ham united", "westham"],
    "Wolverhampton Wanderers": ["wolverhampton", "wolverhampton wanderers",
                                "wolves"],
}


def normalize_team_name(name: str) -> str:
    return " ".join(name.strip().split()).lower()


def build_team_resolver(aliases: Optional[Dict[str, List[str]]] = None) -> Dict[str, str]:
    resolver: Dict[str, str] = {}
    for canonical, variants in (aliases or TEAM_ALIASES).items():
        for variant in variants:
            resolver[normalize_team_name(variant)] = canonical
        resolver[normalize_team_name(canonical)] = canonical
    return resolver


@dataclass
class Match:
    home_team: str
    away_team: str
    home_team_score: int
    away_team_score: int
    match_week: Optional[int] = None

    def is_draw(self) -> bool:
        return self.home_team_score == self.away_team_score

    def winner(self) -> Optional[str]:
        if self.is_draw():
            return None
        return self.home_team if self.home_team_score > self.away_team_score else self.away_team

    def loser(self) -> Optional[str]:
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
            return float("inf")
        return self.goals_scored / self.goals_conceded

    def add_win(self, goals_scored: int, goals_conceded: int) -> None:
        self.played += 1
        self.won += 1
        self.goals_scored += goals_scored
        self.goals_conceded += goals_conceded
        self.points += WIN_POINTS

    def add_draw(self, goals_scored: int, goals_conceded: int) -> None:
        self.played += 1
        self.drawn += 1
        self.goals_scored += goals_scored
        self.goals_conceded += goals_conceded
        self.points += DRAW_POINTS

    def add_loss(self, goals_scored: int, goals_conceded: int) -> None:
        self.played += 1
        self.lost += 1
        self.goals_scored += goals_scored
        self.goals_conceded += goals_conceded
        self.points += LOSS_POINTS


@dataclass
class InputError:

    line: int
    reason: str
    raw: str = ""

    def __str__(self) -> str:
        message = f"line {self.line}: {self.reason}"
        if self.raw:
            message += f" -> raw: {self.raw!r}"
        return message


@dataclass
class LoadReport:
    """Result of parsing a fixtures file: valid matches plus problems found."""

    matches: List[Match]
    errors: List[InputError]
    unknown_teams: List[str]
    schema: str  # one of "4-column", "5-column", "unknown"

    @property
    def ok(self) -> bool:
        return not self.errors and not self.unknown_teams


class LeagueTable:
    def __init__(self) -> None:
        self.teams: Dict[str, TeamStats] = {}

    def _get_or_create_team(self, team_name: str) -> TeamStats:
        if team_name not in self.teams:
            self.teams[team_name] = TeamStats(team_name)
        return self.teams[team_name]

    def process_match(self, match: Match) -> None:
        home_stats = self._get_or_create_team(match.home_team)
        away_stats = self._get_or_create_team(match.away_team)

        if match.is_draw():
            home_stats.add_draw(match.home_team_score, match.away_team_score)
            away_stats.add_draw(match.away_team_score, match.home_team_score)
            return

        if match.home_team_score > match.away_team_score:
            home_stats.add_win(match.home_team_score, match.away_team_score)
            away_stats.add_loss(match.away_team_score, match.home_team_score)
        else:
            away_stats.add_win(match.away_team_score, match.home_team_score)
            home_stats.add_loss(match.home_team_score, match.away_team_score)

    @staticmethod
    def _sort_key(stats: TeamStats):
        # Ranking rule: points, then goal average, then goals scored.
        # The team name is a deterministic display tie-break only (non-rule).
        return (-stats.points, -stats.goal_average(), -stats.goals_scored,
                stats.team_name)

    def get_table(self) -> List[TeamStats]:
        return sorted(self.teams.values(), key=self._sort_key)

    STANDINGS_HEADER = ["Team", "Played", "Won", "Drawn", "Lost",
                        "Goals Scored", "Goals Conceded", "Goal Average",
                        "Points"]

    def to_csv(self) -> str:
        buffer = io.StringIO()
        writer = csv.writer(buffer, lineterminator="\n")
        writer.writerow(self.STANDINGS_HEADER)
        for stats in self.get_table():
            writer.writerow([stats.team_name, stats.played, stats.won,
                             stats.drawn, stats.lost, stats.goals_scored,
                             stats.goals_conceded, stats.goal_average(),
                             stats.points])
        return buffer.getvalue()


class StandingsCalculator:

    @staticmethod
    def _resolve_team_name(raw_name: str, resolver: Dict[str, str]) -> str:
        key = normalize_team_name(raw_name)
        return resolver.get(key, key)

    def load_matches(self, filepath: str, strict: bool = False,
                     resolver: Optional[Dict[str, str]] = None) -> LoadReport:
        resolver = resolver or build_team_resolver()
        lines = self._read_lines(filepath)
        matches: List[Match] = []
        errors: List[InputError] = []
        unknown_teams: List[str] = []
        seen_unknown = set()
        schema: Optional[int] = None

        for line_no, raw in enumerate(lines, start=1):
            if not raw.strip():
                continue  # blank line
            try:
                row = next(csv.reader([raw], skipinitialspace=False))
            except csv.Error as exc:
                errors.append(InputError(line_no, f"CSV parse error: {exc}", raw))
                continue
            if not row or all(not cell.strip() for cell in row):
                continue

            if schema is None:
                kind = self._classify_row(row)
                if kind == "invalid":
                    errors.append(InputError(
                       line_no,
                       f"cannot detect schema from first row with {len(row)} "
                       f"columns (expected 4 or 5)", raw))
                    continue
                schema = len(row)
                if kind == "header":
                    continue

            if len(row) != schema:
                errors.append(InputError(
                    line_no, f"expected {schema} columns, found {len(row)}", raw))
                continue

            cells = [c.strip() for c in row]
            if schema == 5:
                week_text, home_raw, away_raw, hs_text, as_text = cells
            else:
                week_text, home_raw, away_raw, hs_text, as_text = None, *cells

            if not home_raw or not away_raw:
                errors.append(InputError(
                    line_no, "home and away team names must not be empty", raw))
                continue

            home_key = normalize_team_name(home_raw)
            away_key = normalize_team_name(away_raw)
            home = self._resolve_team_name(home_raw, resolver)
            away = self._resolve_team_name(away_raw, resolver)
            for key, raw_name in ((home_key, home_raw), (away_key, away_raw)):
                if key not in resolver and key not in seen_unknown:
                    seen_unknown.add(key)
                    unknown_teams.append(raw_name)

            try:
                hs = int(hs_text)
                as_ = int(as_text)
            except ValueError:
                errors.append(InputError(
                    line_no,
                    f"scores must be integers, found {hs_text!r} and {as_text!r}",
                    raw))
                continue
            if hs < 0 or as_ < 0:
                errors.append(InputError(
                    line_no, "scores must be non-negative integers", raw))
                continue

            mw: Optional[int] = None
            if week_text is not None:
                try:
                    mw = int(week_text)
                except ValueError:
                    errors.append(InputError(
                       line_no,
                       f"match week must be an integer, found {week_text!r}",
                       raw))
                    continue
                if mw < 1:
                    errors.append(InputError(
                       line_no,
                       f"match week must be >= 1, found {week_text!r}", raw))
                    continue

            matches.append(Match(home, away, hs, as_, mw))

        if strict and (errors or unknown_teams):
            details = [str(e) for e in errors]
            details += [f"unknown team name {name!r}" for name in unknown_teams]
            raise ValueError("invalid fixtures input:\n  " + "\n  ".join(details))

        return LoadReport(matches=matches, errors=errors,
                         unknown_teams=unknown_teams,
                         schema=self._schema_label(schema))

    @staticmethod
    def _read_lines(filepath: str) -> List[str]:
        if filepath == "-":
            return sys.stdin.read().splitlines()
        with open(filepath, "r", newline="", encoding="utf-8-sig") as handle:
            return handle.read().splitlines()

    @staticmethod
    def _classify_row(row: List[str]) -> str:
        """Return 'header', 'data' or 'invalid' for the first useful row."""
        if len(row) not in (4, 5):
            return "invalid"
        for cell in row[-2:]:
            try:
                if int(cell.strip()) < 0:
                    return "invalid"
            except ValueError:
                return "header"  # non-numeric scores -> a labelled header row
        return "data"

    @staticmethod
    def _schema_label(schema: Optional[int]) -> str:
        if schema == 5:
            return "5-column"
        if schema == 4:
            return "4-column"
        return "unknown"

    # -- computation & output ---------------------------------------------

    def calculate_standings(self, matches: List[Match]) -> LeagueTable:
        league_table = LeagueTable()
        for match in matches:
            league_table.process_match(match)
        return league_table

    def save_standings_to_csv(self, league_table: LeagueTable,
                              filepath: str) -> None:
        parent = os.path.dirname(os.path.abspath(filepath))
        if parent:
            os.makedirs(parent, exist_ok=True)
        content = league_table.to_csv()
        with open(filepath, "w", newline="", encoding="utf-8") as handle:
            handle.write(content)
            if not content.endswith("\n"):
                handle.write("\n")


# -- command line -----------------------------------------------------------

DEFAULT_INPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "data", "input.csv")
DEFAULT_OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "data", "output.csv")


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="football-league",
        description=f"Compute league standings using the {SEASON} rules "
                    f"(win = {WIN_POINTS}, draw = {DRAW_POINTS}, loss = "
                    f"{LOSS_POINTS}; ranking by points, goal average, goals "
                    f"scored).")
    parser.add_argument("-i", "--input", metavar="PATH", default=None,
                        help="fixtures CSV path, or '-' to read from stdin "
                             f"(default: {DEFAULT_INPUT})")
    parser.add_argument("-o", "--output", metavar="PATH", default=None,
                        help="standings CSV path, or '-' to write to stdout "
                             f"(default: {DEFAULT_OUTPUT})")
    parser.add_argument("--strict", action="store_true",
                        help="abort with exit code 1 on any malformed row or "
                             "unknown team name instead of warning and "
                             "continuing")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    input_path = args.input or DEFAULT_INPUT
    output_path = args.output or DEFAULT_OUTPUT

    calculator = StandingsCalculator()
    try:
        report = calculator.load_matches(input_path, strict=args.strict)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 1

    for err in report.errors:
        print(f"[warn] fixtures {err}", file=sys.stderr)
    for name in report.unknown_teams:
        print(f"[warn] fixtures: unknown team name {name!r} — not in the "
              f"{SEASON} club register; tallied under that name",
              file=sys.stderr)

    table = calculator.calculate_standings(report.matches)

    if output_path == "-":
        sys.stdout.write(table.to_csv())
    else:
        calculator.save_standings_to_csv(table, output_path)
        sys.stdout.write(table.to_csv())
    return 0


if __name__ == "__main__":
    sys.exit(main())