# 2026 Season

## Inputs
- Source: SwimTopia dataclip "TSA: Current Year Meet Results" (via Nathan Roller),
  Stefan van Staveren's `2025 Dual Meet Summary v.3.0` workbook (ranks entering 2026),
  and his `2026 Dual Meet Summary v.4.0` workbook (official score corrections).
- Received: 2026-10-14
- `north_ranks.csv`, `south_ranks.csv` — from `tools/legacy_extract_rank.py` on the 2025 workbook.
  Jewish Community Center is ranked (N38) but swam no 2026 meets; the scheduler drops it.
- `score_overrides.csv` — 11 rain-shortened 7/7/2026 meets recorded by the league as
  1-1 ties (or 1-0), extracted with `tools/legacy_extract_score_overrides.py`.
- `team_addresses.csv`, `team_distances.csv`, `team_drive_minutes.csv` — scraped/built 2026-10-17.

## Run
- Date: 2026-10-17
- Code version (commit): see `git log -- data/2026/output`
- Command: `python src/scheduling.py data/2026 --compare data/2027/input`
- Notes: weights in `config.yaml` were tuned against the committee's approved 2027
  ranking (`data/2027/input/*_ranks.csv`, from the 10/2026 L&S meeting).
  Result: North 28/37 exact (36 within 1, max off 2), South 34/51 exact (45 within 1,
  max off 4), Spearman 0.998–0.999. Remaining differences are adjacent-pair swaps the
  committee resolved with judgement calls (see `output/ranking_report.csv`).
