# 2025 Season

## Inputs
- Source: SwimTopia dataclip (via Stefan, 2026-10-14); ranks entering 2025 from the 2024 workbook
  via `tools/legacy_extract_rank.py`.
- `score_overrides.csv` — empty; dataclip matched the Results sheet.
- Twelve Oaks and Jewish Community Center were ranked but swam no 2025 meets; the engine drops
  them. The committee kept JCC on the 2026 list at N38 (0-0 record), so the 2026 reference has one
  more North team than the engine output.
- Breckenridge and Sweetwater joined (South); declared in `new_teams` and appended at the bottom.

## Run
- Date: 2026-10-17
- Code version (commit): see `git log -- data/2025/output`
- Command: `python src/scheduling.py data/2025 --compare data/2026/input`
- Weights: copied from `data/2026/config.yaml` (tuned on 2026 only — this season is out-of-sample).
- Result vs committee's approved 2026 ranks: North 17/37 exact (35 within 1, max off 2),
  South 27/51 exact (44 within 1, max off 4). Largest misses: Apex (5 → 9), Weldon Ridge (25 → 29).
  Full breakdown in `output/ranking_report.csv` and [docs/accuracy_summary.md](../../docs/accuracy_summary.md).
