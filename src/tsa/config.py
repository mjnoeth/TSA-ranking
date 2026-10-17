"""Season configuration: config.yaml parsing and path resolution."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

LEAGUES = ("North", "South")

DEFAULT_WEIGHTS = {
    # Baseline: points per rank position below the bottom of the league.
    # Keeps a team near where it was; everything else perturbs this.
    "previous_rank": 25.0,
    # In-division record. Points per (win - loss); ties = 0. In practice the
    # winner/loser flags below capture this, so the default is 0.
    "division_record": 0.0,
    # Overall record. Points per (win - loss).
    "overall_record": 15.0,
    # Flat bonus/penalty for finishing first/last in your division.
    "division_winner": 40.0,
    "division_loser": 60.0,
    # Points per point of in-division score differential.
    "division_point_diff": 0.0,
    # Points per point of overall score differential.
    "overall_point_diff": 0.0,
    # Travel burden (mean road miles / drive minutes to other clubs in the
    # league, normalised 0..1 within league). Subtracted. Default 0 = ignored.
    "travel_distance": 0.0,
    "travel_minutes": 0.0,
}

DEFAULT_ADJUST = {
    # Pairwise pass after scoring: a lower-rated team that beat the team
    # directly above it is swapped up, if the rating gap is small enough.
    "hth_enabled": True,
    "hth_min_margin": 1.0,          # ignore direct results closer than this
    "hth_max_rating_gap": 60.0,     # never swap across a gap larger than this
    # Common-opponent point differential, used when the pair did not meet.
    "copd_enabled": True,
    "copd_min_margin": 80.0,        # net COPD must favour the lower team by this much
    "copd_max_rating_gap": 45.0,
    "passes": 3,                    # bubble passes
}


@dataclass
class SeasonConfig:
    year: int
    root: Path                      # data/<year>/
    inputs: dict[str, Path]         # resolved paths; optional ones may be absent
    aliases: dict[str, str]         # alt name -> canonical (ranks) name
    new_teams: dict[str, str]       # team -> league, for clubs not in last year's ranks
    division_size: int
    weights: dict[str, float]
    adjust: dict
    output_dir: Path

    @property
    def input_dir(self) -> Path:
        return self.root / "input"


def load_config(season_dir: Path) -> SeasonConfig:
    season_dir = Path(season_dir)
    cfg_path = season_dir / "config.yaml"
    raw = yaml.safe_load(cfg_path.read_text()) or {}

    year = int(raw.get("year") or season_dir.name)
    input_dir = season_dir / "input"
    inputs_raw = raw.get("inputs", {})

    inputs: dict[str, Path] = {}
    for key, default in (
        ("north_ranks", "north_ranks.csv"),
        ("south_ranks", "south_ranks.csv"),
        ("dataclips", None),
        ("score_overrides", "score_overrides.csv"),
        ("team_addresses", "team_addresses.csv"),
        ("team_distances", "team_distances.csv"),
        ("team_drive_minutes", "team_drive_minutes.csv"),
    ):
        name = inputs_raw.get(key, default)
        if name:
            inputs[key] = input_dir / name
    if "dataclips" not in inputs:
        # Fall back to the single *.csv matching the SwimTopia naming pattern.
        cands = sorted(input_dir.glob("*DATACLIPS*.csv"))
        if len(cands) != 1:
            raise FileNotFoundError(f"set inputs.dataclips in {cfg_path}; found {cands}")
        inputs["dataclips"] = cands[0]

    for key in ("north_ranks", "south_ranks", "dataclips"):
        if not inputs[key].is_file():
            raise FileNotFoundError(f"required input missing: {inputs[key]}")

    weights = {**DEFAULT_WEIGHTS, **(raw.get("weights") or {})}
    unknown = set(weights) - set(DEFAULT_WEIGHTS)
    if unknown:
        raise ValueError(f"unknown weight(s) in {cfg_path}: {sorted(unknown)}")
    adjust = {**DEFAULT_ADJUST, **(raw.get("adjust") or {})}

    return SeasonConfig(
        year=year,
        root=season_dir,
        inputs=inputs,
        aliases={str(k): str(v) for k, v in (raw.get("aliases") or {}).items()},
        new_teams={str(k): str(v) for k, v in (raw.get("new_teams") or {}).items()},
        division_size=int((raw.get("division") or {}).get("size", 4)),
        weights={k: float(v) for k, v in weights.items()},
        adjust=adjust,
        output_dir=season_dir / "output",
    )
