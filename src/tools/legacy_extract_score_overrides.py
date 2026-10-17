#!/usr/bin/env python3
"""Extract official score corrections from a legacy Dual Meet Summary workbook.

The SwimTopia dataclip records the score as it stood when a meet ended. The
league sometimes overrides that (e.g. a rain-shortened meet that never reached
official status is recorded as a 1-1 tie). Stefan applied those corrections by
hand in the workbook's "Results" sheet.

This tool diffs the dataclip against the Results sheet and writes every
disagreement to score_overrides.csv, which the scheduler applies on load.

Usage:
  python src/tools/legacy_extract_score_overrides.py <workbook.xlsx> <dataclips.csv> [--config config.yaml] [--out score_overrides.csv]

--config supplies the season's `aliases:` so dataclip names (e.g. "Abbington
Alligators") match the workbook's canonical names. Dataclip meets with blank
scores are written as overrides too (the official result is the only one).

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
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tsa.data import is_dual_meet  # noqa: E402


def load_results_sheet(path: Path) -> dict[frozenset, tuple[str, float, str, float]]:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    if "Results" not in wb.sheetnames:
        raise SystemExit(f"error: workbook has no 'Results' sheet (has {wb.sheetnames})")
    out = {}
    skipped = 0
    for row in wb["Results"].iter_rows(min_row=2, max_col=5, values_only=True):
        date, winner, wscore, loser, lscore = row
        if not (isinstance(winner, str) and isinstance(loser, str)):
            continue
        if wscore is None or lscore is None:
            skipped += 1
            continue
        out[frozenset((winner.strip(), loser.strip()))] = (str(date)[:10], winner.strip(), float(wscore), loser.strip(), float(lscore))
    if skipped:
        print(f"note: {skipped} Results row(s) have a team but no score; ignored", file=sys.stderr)
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("workbook", type=Path)
    p.add_argument("dataclips", type=Path)
    p.add_argument("--config", type=Path, help="season config.yaml providing name aliases")
    p.add_argument("--out", type=Path, help="default: score_overrides.csv next to the dataclips file")
    args = p.parse_args(argv)
    out = args.out or args.dataclips.parent / "score_overrides.csv"

    aliases: dict[str, str] = {}
    if args.config:
        aliases = {str(k): str(v) for k, v in (yaml.safe_load(args.config.read_text()).get("aliases") or {}).items()}
    canon = lambda n: aliases.get(str(n).strip(), str(n).strip())

    official = load_results_sheet(args.workbook)
    d = pd.read_csv(args.dataclips).dropna(subset=["team1_name", "team2_name"])
    d = d[d.meet_name.map(is_dual_meet)]

    rows = []
    missing = []
    for r in d.itertuples(index=False):
        a, b = canon(r.team1_name), canon(r.team2_name)
        k = frozenset((a, b))
        if k not in official:
            missing.append((a, b))
            continue
        _, w, ws, l, ls = official[k]
        off = {w: ws, l: ls}
        blank = pd.isna(r.team1_score) or pd.isna(r.team2_score)
        if blank or abs(off[a] - r.team1_score) > 0.01 or abs(off[b] - r.team2_score) > 0.01:
            if blank:
                note = "dataclip score blank; official result from Results sheet"
            elif off[a] <= 1 and off[b] <= 1:
                note = "incomplete meet recorded as official result " + ("tie" if off[a] == off[b] else "1-0")
            else:
                note = "official result (from Dual Meet Summary Results sheet)"
            rows.append({
                "date": r.meet_date, "team_a": a, "team_b": b,
                "score_a": f"{off[a]:g}", "score_b": f"{off[b]:g}", "note": note,
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
