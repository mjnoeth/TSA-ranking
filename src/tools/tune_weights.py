#!/usr/bin/env python3
"""Search weights/adjust parameters to best reproduce a reference ranking.

Coordinate-descent over the numeric knobs in config.yaml, scoring each
candidate by mean absolute rank error (plus a small penalty on max error)
against reference north/south_ranks.csv. Prints the best configuration as
YAML you can paste back into config.yaml. Does not modify any files.

Usage:
  python src/tools/tune_weights.py data/2026 data/2027/input [--iters 4] [--seed 0]
"""

from __future__ import annotations

import argparse
import copy
import random
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tsa.config import load_config          # noqa: E402
from tsa.data import load_season            # noqa: E402
from tsa.ranking import rank_season         # noqa: E402
from tsa.report import compare              # noqa: E402

# knob -> candidate values to try (multiplicative/absolute grids)
GRID = {
    ("weights", "previous_rank"):        [5, 10, 15, 20, 25, 30, 40],
    ("weights", "division_record"):      [0, 5, 10, 15, 20, 25, 30, 40, 60],
    ("weights", "overall_record"):       [0, 2, 5, 8, 10, 15, 20],
    ("weights", "division_winner"):      [0, 10, 20, 30, 40, 60, 80],
    ("weights", "division_loser"):       [0, 10, 20, 30, 40, 60, 80],
    ("weights", "division_point_diff"):  [0, 0.02, 0.05, 0.1, 0.2],
    ("weights", "overall_point_diff"):   [0, 0.01, 0.02, 0.05, 0.1, 0.2],
    ("adjust", "hth_min_margin"):        [1, 5, 10, 20],
    ("adjust", "hth_max_rating_gap"):    [0, 10, 20, 30, 45, 60, 90],
    ("adjust", "copd_min_margin"):       [10, 20, 40, 60, 100],
    ("adjust", "copd_max_rating_gap"):   [0, 10, 20, 30, 45],
    ("adjust", "passes"):                [1, 2, 3, 5],
}
# Grid applied to every metric declared in config `metrics:` when --tune-metrics is set.
METRIC_GRID = [0, 10, 20, 40, 60, 100]


def _get(cfg, section, knob):
    if section == "metrics":
        return next(m for m in cfg.metrics if m.name == knob).weight
    return getattr(cfg, section)[knob]


def _set(cfg, section, knob, val):
    if section == "metrics":
        next(m for m in cfg.metrics if m.name == knob).weight = float(val)
    else:
        getattr(cfg, section)[knob] = float(val) if section == "weights" else val


def score(cfg, season, ref_dir) -> tuple[float, dict]:
    stats = rank_season(season, cfg)
    res = compare(stats, ref_dir, cfg.aliases)
    mae = sum(r["mae"] * r["n"] for r in res.values()) / sum(r["n"] for r in res.values())
    mx = max(r["max"] for r in res.values())
    return mae + 0.05 * mx, res


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("season_dir", type=Path)
    p.add_argument("ref_dir", type=Path)
    p.add_argument("--iters", type=int, default=4, help="coordinate-descent sweeps")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--tune-metrics", action="store_true",
                   help="also search weights of metrics declared in config.yaml (default: leave as configured)")
    args = p.parse_args(argv)

    cfg = load_config(args.season_dir)
    season = load_season(cfg)
    rng = random.Random(args.seed)
    grid = dict(GRID)
    if args.tune_metrics:
        for m in cfg.metrics:
            if m.file.is_file():
                grid[("metrics", m.name)] = METRIC_GRID

    best_obj, res = score(cfg, season, args.ref_dir)
    print(f"start: obj {best_obj:.3f}  " + "  ".join(f"{l} MAE {r['mae']:.2f} exact {r['exact']}/{r['n']}" for l, r in res.items()))

    for sweep in range(args.iters):
        keys = list(grid)
        rng.shuffle(keys)
        improved = False
        for section, knob in keys:
            current = _get(cfg, section, knob)
            for val in grid[(section, knob)]:
                if val == current:
                    continue
                trial = copy.deepcopy(cfg)
                _set(trial, section, knob, val)
                obj, r = score(trial, season, args.ref_dir)
                if obj < best_obj - 1e-9:
                    best_obj, cfg, res, improved = obj, trial, r, True
                    print(f"  sweep {sweep + 1}: {section}.{knob}={val}  obj {obj:.3f}  "
                          + "  ".join(f"{l} MAE {x['mae']:.2f} exact {x['exact']}" for l, x in r.items()))
        if not improved:
            break

    print("\nbest:")
    out = {"weights": cfg.weights, "adjust": cfg.adjust}
    if cfg.metrics:
        out["metrics"] = {m.name: {"weight": m.weight} for m in cfg.metrics}
    print(yaml.safe_dump(out, sort_keys=False))
    for league, r in res.items():
        print(f"{league}: {r['exact']}/{r['n']} exact, {r['within1']} within 1, {r['within2']} within 2, "
              f"MAE {r['mae']:.2f}, max {r['max']}, rho {r['rho']:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
