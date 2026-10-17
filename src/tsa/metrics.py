"""Pluggable per-team metrics declared in config.yaml.

Anything that is "one number per team" can be added to the rating without
code changes:

    metrics:
      team_size:
        file: team_metrics.csv          # CSV with a `team` column
        column: swimmers
        normalize: minmax_league        # none | minmax_league | zscore_league
        direction: higher_is_better     # or lower_is_better
        weight: 0.0
      travel_distance:
        file: team_distances.csv
        source: matrix_row_mean         # square team x team matrix -> mean of row
        normalize: minmax_league
        direction: lower_is_better
        weight: 0.0

Each metric contributes ``weight * signed_normalised_value`` to the rating and
appears as a ``c_<name>`` column in ranking_report.csv.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from statistics import mean, pstdev
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from .data import Season

SOURCES = ("column", "matrix_row_mean")
NORMALIZERS = ("none", "minmax_league", "zscore_league")
DIRECTIONS = ("higher_is_better", "lower_is_better")


@dataclass
class MetricSpec:
    name: str
    file: Path
    source: str = "column"
    column: str | None = None
    normalize: str = "minmax_league"
    direction: str = "higher_is_better"
    weight: float = 0.0
    required: bool = False          # if False, a missing file disables the metric

    @classmethod
    def from_config(cls, name: str, raw: dict, input_dir: Path) -> "MetricSpec":
        if "file" not in raw:
            raise ValueError(f"metrics.{name}: 'file' is required")
        spec = cls(
            name=name,
            file=input_dir / str(raw["file"]),
            source=str(raw.get("source", "column")),
            column=raw.get("column"),
            normalize=str(raw.get("normalize", "minmax_league")),
            direction=str(raw.get("direction", "higher_is_better")),
            weight=float(raw.get("weight", 0.0)),
            required=bool(raw.get("required", False)),
        )
        if spec.source not in SOURCES:
            raise ValueError(f"metrics.{name}.source must be one of {SOURCES}")
        if spec.normalize not in NORMALIZERS:
            raise ValueError(f"metrics.{name}.normalize must be one of {NORMALIZERS}")
        if spec.direction not in DIRECTIONS:
            raise ValueError(f"metrics.{name}.direction must be one of {DIRECTIONS}")
        if spec.source == "column" and not spec.column:
            raise ValueError(f"metrics.{name}: 'column' is required when source is 'column'")
        return spec


@dataclass
class MetricValues:
    spec: MetricSpec
    raw: dict[str, float]           # team -> value as read
    signed: dict[str, float]        # team -> normalised, sign-adjusted (higher = better)


def _canon(name: str, aliases: dict[str, str]) -> str:
    name = str(name).strip()
    return aliases.get(name, name)


def _read_column(spec: MetricSpec, aliases: dict[str, str]) -> dict[str, float]:
    df = pd.read_csv(spec.file)
    if "team" not in df.columns:
        raise ValueError(f"{spec.file}: needs a 'team' column")
    if spec.column not in df.columns:
        raise ValueError(f"{spec.file}: no column {spec.column!r}; has {list(df.columns)}")
    out = {}
    for team, val in zip(df["team"], df[spec.column]):
        if pd.notna(val):
            out[_canon(team, aliases)] = float(val)
    return out


def _read_matrix_row_mean(spec: MetricSpec, season: Season, aliases: dict[str, str]) -> dict[str, float]:
    """Square team x team matrix -> mean of each row over the *other clubs in
    the same league* (travel burden to your own league, not the whole TSA)."""
    df = pd.read_csv(spec.file, index_col=0).astype(float)
    df.index = [_canon(i, aliases) for i in df.index]
    df.columns = [_canon(c, aliases) for c in df.columns]
    out = {}
    for league in {t.league for t in season.teams.values()}:
        names = [t.name for t in season.league_teams(league) if t.name in df.index]
        for n in names:
            others = [o for o in names if o != n]
            out[n] = float(df.loc[n, others].mean()) if others else 0.0
    return out


def _normalise(spec: MetricSpec, season: Season, raw: dict[str, float]) -> dict[str, float]:
    signed: dict[str, float] = {}
    sign = 1.0 if spec.direction == "higher_is_better" else -1.0
    for league in {t.league for t in season.teams.values()}:
        names = [t.name for t in season.league_teams(league)]
        vals = {n: raw[n] for n in names if n in raw}
        if not vals:
            continue
        if spec.normalize == "none":
            norm = dict(vals)
        elif spec.normalize == "minmax_league":
            lo, hi = min(vals.values()), max(vals.values())
            norm = {n: (v - lo) / (hi - lo) if hi > lo else 0.0 for n, v in vals.items()}
        else:  # zscore_league
            mu, sd = mean(vals.values()), pstdev(vals.values())
            norm = {n: (v - mu) / sd if sd > 0 else 0.0 for n, v in vals.items()}
        for n, v in norm.items():
            signed[n] = sign * v
    return signed


def load_metrics(specs: list[MetricSpec], season: Season, aliases: dict[str, str]) -> dict[str, MetricValues]:
    out: dict[str, MetricValues] = {}
    for spec in specs:
        if not spec.file.is_file():
            if spec.required or spec.weight != 0:
                raise FileNotFoundError(f"metrics.{spec.name}: {spec.file} not found")
            continue    # optional, weight 0 -> silently skip
        raw = (_read_matrix_row_mean(spec, season, aliases) if spec.source == "matrix_row_mean"
               else _read_column(spec, aliases))
        missing = sorted(set(season.teams) - set(raw))
        if missing:
            raise ValueError(f"metrics.{spec.name}: no value for {missing} in {spec.file}; add aliases or rows")
        out[spec.name] = MetricValues(spec=spec, raw=raw, signed=_normalise(spec, season, raw))
    return out
