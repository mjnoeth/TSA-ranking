"""Load season inputs into plain data structures.

Canonical team names are those in the ranks CSVs. Every other source
(dataclips, addresses, distance matrices) is mapped through ``aliases``.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from .config import LEAGUES, SeasonConfig


@dataclass
class Team:
    name: str
    league: str
    rank: int                   # rank entering this season (1 = strongest)
    division: int = 0           # assigned by assign_divisions()


@dataclass
class Meet:
    date: str
    team_a: str
    team_b: str
    score_a: float
    score_b: float
    overridden: bool = False

    def margin_for(self, team: str) -> float:
        """Signed point margin from ``team``'s perspective."""
        return (self.score_a - self.score_b) if team == self.team_a else (self.score_b - self.score_a)

    def opponent_of(self, team: str) -> str:
        return self.team_b if team == self.team_a else self.team_a

    def result_for(self, team: str) -> str:
        m = self.margin_for(team)
        return "W" if m > 0 else "L" if m < 0 else "T"


@dataclass
class Season:
    year: int
    teams: dict[str, Team]
    meets: list[Meet]
    division_size: int
    dropped: list[str] = field(default_factory=list)   # in ranks but swam no meets
    added: list[str] = field(default_factory=list)     # swam but not in ranks

    def league_teams(self, league: str) -> list[Team]:
        return sorted((t for t in self.teams.values() if t.league == league), key=lambda t: t.rank)

    def meets_for(self, team: str) -> list[Meet]:
        return [m for m in self.meets if team in (m.team_a, m.team_b)]

    def division_mates(self, team: str) -> list[str]:
        t = self.teams[team]
        return [o.name for o in self.teams.values()
                if o.league == t.league and o.division == t.division and o.name != team]

    def is_division_meet(self, meet: Meet) -> bool:
        a, b = self.teams[meet.team_a], self.teams[meet.team_b]
        return a.league == b.league and a.division == b.division


# ---------------------------------------------------------------------------

def _canon(name: str, aliases: dict[str, str]) -> str:
    name = name.strip()
    return aliases.get(name, name)


def load_ranks(path: Path, league: str) -> list[Team]:
    teams = []
    with path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            teams.append(Team(name=row["team"].strip(), league=league, rank=int(row["rank"])))
    ranks = [t.rank for t in teams]
    if sorted(ranks) != list(range(1, len(ranks) + 1)):
        raise ValueError(f"{path}: ranks are not contiguous 1..N")
    return teams


# Dataclip rows that are not TSA dual meets (optional/championship meets are
# excluded from rankings per the committee methodology).
NON_DUAL_MEET_PATTERNS = ("TSA Champs", "Cary City", "City Meet", "Championship")


def is_dual_meet(meet_name: str) -> bool:
    name = str(meet_name)
    return name != "BYE" and not any(p.lower() in name.lower() for p in NON_DUAL_MEET_PATTERNS)


def load_dataclips(path: Path, aliases: dict[str, str]) -> list[Meet]:
    d = pd.read_csv(path)
    d = d.dropna(subset=["team1_name", "team2_name"])
    d = d[d.meet_name.map(is_dual_meet)]
    meets = []
    for r in d.itertuples(index=False):
        # Blank scores (meet never finalised in SwimTopia) are kept as NaN so a
        # score_overrides.csv row can supply the league's official result.
        meets.append(Meet(
            date=str(r.meet_date),
            team_a=_canon(r.team1_name, aliases),
            team_b=_canon(r.team2_name, aliases),
            score_a=float(r.team1_score) if pd.notna(r.team1_score) else float("nan"),
            score_b=float(r.team2_score) if pd.notna(r.team2_score) else float("nan"),
        ))
    return meets


def apply_overrides(meets: list[Meet], path: Path | None, aliases: dict[str, str]) -> int:
    if not path or not path.is_file():
        return 0
    by_pair = {frozenset((m.team_a, m.team_b)): m for m in meets}
    n = 0
    with path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            a, b = _canon(row["team_a"], aliases), _canon(row["team_b"], aliases)
            m = by_pair.get(frozenset((a, b)))
            if m is None:
                raise ValueError(f"{path}: override for {a} vs {b} matches no meet")
            sa, sb = float(row["score_a"]), float(row["score_b"])
            if m.team_a == a:
                m.score_a, m.score_b = sa, sb
            else:
                m.score_a, m.score_b = sb, sa
            m.overridden = True
            n += 1
    return n


def assign_divisions(season: Season) -> None:
    """Fill divisions of ``division_size`` from the top; the remainder is
    absorbed by making the bottom divisions one team smaller (TSA practice:
    4-team divisions with 3-team divisions at the bottom)."""
    s = season.division_size
    for league in LEAGUES:
        teams = season.league_teams(league)
        n = len(teams)
        n_small = (-n) % s                 # how many divisions get s-1 teams
        n_full = (n - n_small * (s - 1)) // s
        sizes = [s] * n_full + [s - 1] * n_small
        i = 0
        for div_no, size in enumerate(sizes, start=1):
            for t in teams[i:i + size]:
                t.division = div_no
            i += size
        assert i == n, f"{league}: division sizes {sizes} do not cover {n} teams"


def load_season(cfg: SeasonConfig) -> Season:
    teams: dict[str, Team] = {}
    for league, key in (("North", "north_ranks"), ("South", "south_ranks")):
        for t in load_ranks(cfg.inputs[key], league):
            if t.name in teams:
                raise ValueError(f"team {t.name!r} appears in both leagues")
            teams[t.name] = t

    meets = load_dataclips(cfg.inputs["dataclips"], cfg.aliases)
    apply_overrides(meets, cfg.inputs.get("score_overrides"), cfg.aliases)
    unscored = [m for m in meets if m.score_a != m.score_a or m.score_b != m.score_b]   # NaN check
    if unscored:
        ex = ", ".join(f"{m.team_a} vs {m.team_b} ({m.date})" for m in unscored[:5])
        raise ValueError(f"{len(unscored)} meet(s) have no score in the dataclip and no override: {ex}"
                         + (" ..." if len(unscored) > 5 else "") + ". Add rows to score_overrides.csv.")

    played = {m.team_a for m in meets} | {m.team_b for m in meets}

    # Clubs that swam but are not ranked: must be declared in config.new_teams.
    added = sorted(played - set(teams))
    for name in added:
        league = cfg.new_teams.get(name)
        if not league:
            raise ValueError(
                f"{name!r} appears in dataclips but not in ranks; add it to new_teams in config.yaml "
                f"(e.g. new_teams: {{{name!r}: North}})"
            )
        teams[name] = Team(name=name, league=league, rank=10**6)   # placed at bottom below

    # Ranked clubs that swam nothing are dropped (e.g. folded before the season).
    dropped = sorted(set(teams) - played)
    for name in dropped:
        del teams[name]

    # Renumber ranks contiguously within each league, new teams at the bottom
    # in config order.
    for league in LEAGUES:
        lt = [t for t in teams.values() if t.league == league]
        order = {n: i for i, n in enumerate(cfg.new_teams)}
        lt.sort(key=lambda t: (t.rank, order.get(t.name, 0)))
        for i, t in enumerate(lt, start=1):
            t.rank = i

    season = Season(
        year=cfg.year, teams=teams, meets=meets, division_size=cfg.division_size,
        dropped=dropped, added=added,
    )
    assign_divisions(season)
    return season
