#!/usr/bin/env python3
"""TSA next-season ranking from this season's results.

Usage:
  python src/scheduling.py data/2026                 # writes data/2026/output/
  python src/scheduling.py data/2026 --compare data/2027/input
  python src/scheduling.py data/2026 --dry-run       # print ranks, write nothing

Inputs are read from data/<year>/input/ as declared in data/<year>/config.yaml:
  north_ranks.csv, south_ranks.csv   rank entering this season (required)
  <dataclips>.csv                    SwimTopia meet results (required)
  score_overrides.csv                official corrections to dataclip scores
  team_distances.csv                 road miles matrix (optional, weight 0 by default)
  team_drive_minutes.csv             drive-time matrix (optional, weight 0 by default)

Outputs in data/<year>/output/:
  north_ranks.csv, south_ranks.csv   next season's rank (same format as input)
  ranking_report.csv                 per-team records, rating components, adjustments
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from tsa.config import LEAGUES, load_config          # noqa: E402
from tsa.data import load_season                     # noqa: E402
from tsa.ranking import rank_season                  # noqa: E402
from tsa.report import compare, format_compare, write_ranks, write_report   # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("season_dir", type=Path, help="data/<year> directory containing config.yaml and input/")
    p.add_argument("--compare", type=Path, metavar="DIR",
                   help="directory with reference north_ranks.csv/south_ranks.csv to score against")
    p.add_argument("--dry-run", action="store_true", help="do not write output files")
    p.add_argument("--quiet", "-q", action="store_true", help="suppress the ranking printout")
    args = p.parse_args(argv)

    cfg = load_config(args.season_dir)
    season = load_season(cfg)
    stats = rank_season(season, cfg)

    print(f"{cfg.year} season: {len(season.teams)} teams, {len(season.meets)} meets "
          f"({sum(m.overridden for m in season.meets)} overridden)")
    if season.dropped:
        print(f"  dropped (ranked but swam no meets): {season.dropped}")
    if season.added:
        print(f"  added (swam but not ranked): {season.added}")

    if not args.quiet:
        for league in LEAGUES:
            print(f"\n{league}")
            for s in sorted((s for s in stats.values() if s.league == league), key=lambda s: s.new_rank):
                chg = s.prev_rank - s.new_rank
                flag = " W" if s.div_winner else " L" if s.div_loser else "  "
                print(f"  {s.new_rank:3d} ({s.prev_rank:3d} {chg:+3d}){flag} {s.name:34s} "
                      f"div {s.div_record:6s} ovr {s.ovr_record:6s} pd {s.ovr_pd:+5g} rating {s.rating:7.1f}")

    if not args.dry_run:
        paths = write_ranks(stats, cfg.output_dir)
        rep = write_report(season, stats, cfg, cfg.output_dir)
        print(f"\nwrote {', '.join(str(p) for p in paths.values())} and {rep}")

    if args.compare:
        res = compare(stats, args.compare, cfg.aliases)
        print(f"\nComparison against {args.compare}:")
        print(format_compare(res))
    return 0


if __name__ == "__main__":
    sys.exit(main())
