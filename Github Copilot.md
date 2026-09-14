# GitHub Copilot Project Instructions

## Project Overview

This project is a command-line application written in Python that calculates football league standings from match results provided in a CSV file.

The application is based on the requirements provided in the SPAN coding assessment. It models matches, team statistics, league-table processing, CSV input/output, and the calculation of final standings.

## Technology

* Python 3
* Standard Python library where practical
* `pytest` for automated tests
* CSV files for input and output

## Project Structure

The solution separates responsibilities into the following concepts:

* `Match` — represents an individual football match and determines whether the match was a draw, winner, or loser.
* `TeamStats` — stores and updates statistics for an individual team.
* `LeagueTable` — maintains teams and processes match results.
* `StandingsCalculator` — handles CSV loading, standings calculation, and saving the output.

## AI Collaboration Guidelines

When assisting with this project:

1. Understand the assessment requirements before suggesting implementation changes.
2. Do not rewrite working code unnecessarily.
3. Explain proposed changes before making significant modifications.
4. Identify potential edge cases and recommend appropriate tests.
5. Prefer simple, readable Python over unnecessary abstractions.
6. Avoid introducing third-party dependencies unless there is a clear reason.
7. Maintain platform-independent behaviour because the application must run in a Unix-like environment.
8. Preserve the separation of responsibilities represented by the UML.
9. Do not remove or weaken existing tests to make the implementation pass.
10. When identifying a potential problem, distinguish between:

* a requirement from the specification,
* a discrepancy with the UML,
* a potential edge case,
* and an optional improvement.

11. The developer remains responsible for reviewing and deciding whether AI suggestions should be accepted.

## Testing

Changes to behaviour should be supported by automated tests.

Tests should cover:

* Match result determination
* Draws, wins and losses
* Team statistics
* League-table calculation
* Sorting and tie-breaking
* CSV loading
* Invalid or malformed input where relevant
* End-to-end input/output behaviour

## Code Quality

Prioritise:

* Readability
* Small, focused methods
* Clear naming
* Type hints where useful
* Appropriate error handling
* Deterministic output
* Testable behaviour

Avoid adding complexity that is not justified by the requirements.

## Important Assessment Constraint

The final implementation must be understandable by the developer submitting it. AI suggestions must be reviewed, tested, and either accepted with understanding or rejected with an explicit reason.
