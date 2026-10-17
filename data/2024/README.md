# 2024 Season

## Inputs
- Source: SwimTopia dataclip (via Stefan, 2026-10-14); ranks entering 2024 from the 2023 workbook
  via `tools/legacy_extract_rank.py`.
- `score_overrides.csv` — empty; dataclip matched the Results sheet for every dual meet.
- TSA Champs / Cary City rows in the dataclip are ignored (not dual meets).

## Run
- Date: 2026-10-17
- Code version (commit): see `git log -- data/2024/output`
- Command: `python src/scheduling.py data/2024 --compare data/2025/input`
- Weights: copied from `data/2026/config.yaml` (tuned on 2026 only — this season is out-of-sample).
- Result vs committee's approved 2025 ranks: North 21/38 exact (35 within 1, max off 2),
  South 34/50 exact (48 within 1, max off 2). Every team within 2 places.
  Full breakdown in `output/ranking_report.csv` and [docs/accuracy_summary.md](../../docs/accuracy_summary.md).
