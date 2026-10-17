#!/usr/bin/env python3
"""Extract official score corrections from a legacy Dual Meet Summary workbook.

The SwimTopia dataclip records the score as it stood when a meet ended. The
league sometimes overrides that (e.g. a rain-shortened meet that never reached
official status is recorded as a 1-1 tie). Stefan applied those corrections by
hand in the workbook's "Results" sheet.

This tool diffs the dataclip against the Results sheet and writes every
disagreement to score_overrides.csv, which the scheduler applies on load.

Usage:
  python src/tools/legacy_extract_score_overrides.py <workbook.xlsx> <dataclips.csv> [--out score_overrides.csv]

Output columns: date, team_a, team_b, score_a, score_b, note
"""

from __future__ import annotations

import argparse
import csv
import sys
import warnings
from pathlib import Path

import openpyxl
import pandas as pd


def load_results_sheet(path: Path) -> dict[frozenset, tuple[str, float, str, float]]:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    if "Results" not in wb.sheetnames:
        raise SystemExit(f"error: workbook has no 'Results' sheet (has {wb.sheetnames})")
    out = {}
    for row in wb["Results"].iter_rows(min_row=2, max_col=5, values_only=True):
        date, winner, wscore, loser, lscore = row
        if not (isinstance(winner, str) and isinstance(loser, str)):
            continue
        out[frozenset((winner.strip(), loser.strip()))] = (str(date)[:10], winner.strip(), float(wscore), loser.strip(), float(lscore))
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("workbook", type=Path)
    p.add_argument("dataclips", type=Path)
    p.add_argument("--out", type=Path, help="default: score_overrides.csv next to the dataclips file")
    args = p.parse_args(argv)
    out = args.out or args.dataclips.parent / "score_overrides.csv"

    official = load_results_sheet(args.workbook)
    d = pd.read_csv(args.dataclips).dropna(subset=["team1_name", "team2_name", "team1_score", "team2_score"])
    d = d[d.meet_name != "BYE"]

    rows = []
    missing = []
    for r in d.itertuples(index=False):
        k = frozenset((r.team1_name, r.team2_name))
        if k not in official:
            missing.append((r.team1_name, r.team2_name))
            continue
        _, w, ws, l, ls = official[k]
        off = {w: ws, l: ls}
        if abs(off[r.team1_name] - r.team1_score) > 0.01 or abs(off[r.team2_name] - r.team2_score) > 0.01:
            note = "official result (from Dual Meet Summary Results sheet)"
            if off[r.team1_name] <= 1 and off[r.team2_name] <= 1:
                note = "incomplete meet recorded as official result " + ("tie" if off[r.team1_name] == off[r.team2_name] else "1-0")
            rows.append({
                "date": r.meet_date, "team_a": r.team1_name, "team_b": r.team2_name,
                "score_a": f"{off[r.team1_name]:g}", "score_b": f"{off[r.team2_name]:g}", "note": note,
            })

    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["date", "team_a", "team_b", "score_a", "score_b", "note"])
        w.writeheader()
        w.writerows(rows)
    print(f"{len(d)} dataclip meets, {len(official)} official results; {len(rows)} override(s) -> {out}")
    if missing:
        print(f"warning: {len(missing)} dataclip meet(s) not found in Results sheet: {missing}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
