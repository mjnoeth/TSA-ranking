"""Smoke tests for the ranking engine. Run: .venv/bin/python -m pytest tests/"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tsa.config import DEFAULT_ADJUST, DEFAULT_WEIGHTS  # noqa: E402
from tsa.data import Meet, Season, Team, assign_divisions  # noqa: E402
from tsa.ranking import compute_stats, copd  # noqa: E402


def _season(n_north: int, meets: list[Meet] | None = None) -> Season:
    teams = {f"N{i}": Team(f"N{i}", "North", i) for i in range(1, n_north + 1)}
    s = Season(year=2000, teams=teams, meets=meets or [], division_size=4)
    assign_divisions(s)
    return s


def test_division_sizes_fill_fours_then_threes_at_bottom():
    for n, expected in ((37, [4] * 7 + [3] * 3), (51, [4] * 12 + [3]), (38, [4] * 8 + [3] * 2), (40, [4] * 10)):
        s = _season(n)
        sizes = {}
        for t in s.teams.values():
            sizes[t.division] = sizes.get(t.division, 0) + 1
        assert [sizes[d] for d in sorted(sizes)] == expected, n


def test_division_winner_tiebreak_on_point_diff():
    # N1-N4 are division 1. N1 and N2 both 2-0-1; N1 has the bigger differential.
    meets = [
        Meet("d", "N1", "N3", 200, 100), Meet("d", "N1", "N4", 200, 100), Meet("d", "N1", "N2", 1, 1),
        Meet("d", "N2", "N3", 150, 140), Meet("d", "N2", "N4", 150, 140),
        Meet("d", "N3", "N4", 120, 100),
    ]
    s = _season(4, meets)
    st = compute_stats(s)
    assert st["N1"].div_winner and not st["N2"].div_winner
    assert st["N4"].div_loser
    assert st["N1"].div_record == "2-0-1" and st["N4"].div_record == "0-3"


def test_copd_is_net_margin_over_common_opponents():
    meets = [Meet("d", "A", "K", 150, 100), Meet("d", "B", "K", 120, 100), Meet("d", "A", "Z", 100, 90)]
    teams = {n: Team(n, "North", i) for i, n in enumerate(["A", "B", "K", "Z"], 1)}
    s = Season(year=2000, teams=teams, meets=meets, division_size=4)
    net, common = copd(s, "A", "B")
    assert common == ["K"] and net == 30


def test_defaults_are_complete():
    assert set(DEFAULT_WEIGHTS) >= {"previous_rank", "division_winner", "division_loser", "travel_distance", "travel_minutes"}
    assert "passes" in DEFAULT_ADJUST
