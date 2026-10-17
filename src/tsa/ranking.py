"""Objective ranking: per-team season stats, weighted rating, pairwise adjustment.

Follows the committee's stated methodology (docs/prototype_planning):
  1. In-division record / division winner-loser status  (primary)
  2. Head-to-head result between the two teams            (secondary)
  3. Point differential
  4. Common-opponent point differential (COPD) when the pair did not meet

Every factor is a configurable weight (config.yaml -> weights) so the
committee can argue about numbers instead of mechanics.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .config import LEAGUES, SeasonConfig
from .data import Meet, Season


@dataclass
class TeamStats:
    name: str
    league: str
    prev_rank: int
    division: int
    div_w: int = 0
    div_l: int = 0
    div_t: int = 0
    ovr_w: int = 0
    ovr_l: int = 0
    ovr_t: int = 0
    div_pd: float = 0.0          # in-division point differential
    ovr_pd: float = 0.0          # overall point differential
    div_winner: bool = False
    div_loser: bool = False
    travel_miles: float | None = None     # mean road miles to other league clubs
    travel_minutes: float | None = None
    travel_miles_norm: float = 0.0        # 0..1 within league (0 = most central)
    travel_minutes_norm: float = 0.0
    rating: float = 0.0
    components: dict[str, float] = field(default_factory=dict)
    new_rank: int = 0
    adjustments: list[str] = field(default_factory=list)   # human-readable log

    @property
    def div_record(self) -> str:
        return f"{self.div_w}-{self.div_l}" + (f"-{self.div_t}" if self.div_t else "")

    @property
    def ovr_record(self) -> str:
        return f"{self.ovr_w}-{self.ovr_l}" + (f"-{self.ovr_t}" if self.ovr_t else "")


# ---------------------------------------------------------------------------
# Stats

def compute_stats(season: Season) -> dict[str, TeamStats]:
    stats = {
        t.name: TeamStats(name=t.name, league=t.league, prev_rank=t.rank, division=t.division)
        for t in season.teams.values()
    }
    for m in season.meets:
        in_div = season.is_division_meet(m)
        for team in (m.team_a, m.team_b):
            s = stats[team]
            margin = m.margin_for(team)
            res = m.result_for(team)
            s.ovr_pd += margin
            s.ovr_w += res == "W"; s.ovr_l += res == "L"; s.ovr_t += res == "T"
            if in_div:
                s.div_pd += margin
                s.div_w += res == "W"; s.div_l += res == "L"; s.div_t += res == "T"

    # Division winner / loser: best / worst in-division record, ties broken by
    # in-division point differential (matches committee practice, e.g. 2026
    # South D12 where two 2-0-1 teams were split on differential).
    for league in LEAGUES:
        by_div: dict[int, list[TeamStats]] = {}
        for s in stats.values():
            if s.league == league:
                by_div.setdefault(s.division, []).append(s)
        for members in by_div.values():
            key = lambda s: (s.div_w - s.div_l, s.div_pd)
            members.sort(key=key, reverse=True)
            members[0].div_winner = True
            members[-1].div_loser = True

    _compute_travel(season, stats)
    return stats


def _compute_travel(season: Season, stats: dict[str, TeamStats]) -> None:
    for df, attr in ((season.distances, "miles"), (season.drive_minutes, "minutes")):
        if df is None:
            continue
        for league in LEAGUES:
            names = [t.name for t in season.league_teams(league)]
            vals = {}
            for n in names:
                others = [o for o in names if o != n]
                vals[n] = float(df.loc[n, others].mean())
                setattr(stats[n], f"travel_{attr}", vals[n])
            lo, hi = min(vals.values()), max(vals.values())
            for n, v in vals.items():
                setattr(stats[n], f"travel_{attr}_norm", (v - lo) / (hi - lo) if hi > lo else 0.0)


# ---------------------------------------------------------------------------
# Rating

def compute_ratings(season: Season, stats: dict[str, TeamStats], weights: dict[str, float]) -> None:
    for league in LEAGUES:
        n = len(season.league_teams(league))
        for s in stats.values():
            if s.league != league:
                continue
            c = {
                "previous_rank": weights["previous_rank"] * (n - s.prev_rank + 1),
                "division_record": weights["division_record"] * (s.div_w - s.div_l),
                "overall_record": weights["overall_record"] * (s.ovr_w - s.ovr_l),
                "division_winner": weights["division_winner"] * s.div_winner,
                "division_loser": -weights["division_loser"] * s.div_loser,
                "division_point_diff": weights["division_point_diff"] * s.div_pd,
                "overall_point_diff": weights["overall_point_diff"] * s.ovr_pd,
                "travel_distance": -weights["travel_distance"] * s.travel_miles_norm,
                "travel_minutes": -weights["travel_minutes"] * s.travel_minutes_norm,
            }
            s.components = c
            s.rating = sum(c.values())


# ---------------------------------------------------------------------------
# Pairwise adjustment (HTH, then COPD)

def _hth(season: Season, a: str, b: str) -> Meet | None:
    for m in season.meets:
        if {m.team_a, m.team_b} == {a, b}:
            return m
    return None


def copd(season: Season, a: str, b: str) -> tuple[float, list[str]]:
    """Net common-opponent point differential, positive favours ``a``."""
    ma = {m.opponent_of(a): m.margin_for(a) for m in season.meets_for(a)}
    mb = {m.opponent_of(b): m.margin_for(b) for m in season.meets_for(b)}
    common = sorted(set(ma) & set(mb) - {a, b})
    return sum(ma[o] - mb[o] for o in common), common


def adjust_order(season: Season, stats: dict[str, TeamStats], order: list[str], adj: dict) -> list[str]:
    """Bubble passes over a league's rating order. For each adjacent pair
    (upper, lower): swap if the lower team beat the upper directly, or — if
    they did not meet — if COPD clearly favours the lower team. Both are
    gated by a maximum rating gap so clear-cut ratings are not overturned."""
    order = list(order)
    for _ in range(int(adj["passes"])):
        changed = False
        for i in range(len(order) - 1):
            up, lo = order[i], order[i + 1]
            gap = stats[up].rating - stats[lo].rating
            m = _hth(season, up, lo)
            if m is not None:
                if not adj["hth_enabled"]:
                    continue
                margin = m.margin_for(lo)
                if margin >= adj["hth_min_margin"] and gap <= adj["hth_max_rating_gap"]:
                    order[i], order[i + 1] = lo, up
                    note = f"HTH: {lo} beat {up} by {margin:g} (rating gap {gap:.0f})"
                    stats[lo].adjustments.append("moved up — " + note)
                    stats[up].adjustments.append("moved down — " + note)
                    changed = True
            elif adj["copd_enabled"]:
                net, common = copd(season, lo, up)
                if common and net >= adj["copd_min_margin"] and gap <= adj["copd_max_rating_gap"]:
                    order[i], order[i + 1] = lo, up
                    note = f"COPD: {lo} over {up} by net {net:g} via {', '.join(common)} (rating gap {gap:.0f})"
                    stats[lo].adjustments.append("moved up — " + note)
                    stats[up].adjustments.append("moved down — " + note)
                    changed = True
        if not changed:
            break
    return order


# ---------------------------------------------------------------------------

def rank_season(season: Season, cfg: SeasonConfig) -> dict[str, TeamStats]:
    stats = compute_stats(season)
    compute_ratings(season, stats, cfg.weights)
    for league in LEAGUES:
        names = [t.name for t in season.league_teams(league)]
        # Stable tiebreak on equal rating: previous rank.
        order = sorted(names, key=lambda n: (-stats[n].rating, stats[n].prev_rank))
        order = adjust_order(season, stats, order, cfg.adjust)
        for i, n in enumerate(order, start=1):
            stats[n].new_rank = i
    return stats
