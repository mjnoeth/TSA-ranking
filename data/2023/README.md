# 2023 Season

## Inputs
- Source: SwimTopia dataclip (via Stefan, 2026-10-14) and Stefan's `2022 Dual Meet Summary v.1.0` workbook.
- `north_ranks.csv`, `south_ranks.csv` — the 2022 workbook's Report sheets are unfilled (`#N/A`),
  so the ranks *entering* 2023 were taken from the **2023** workbook's Report sheets, column D
  ("2023 Rank"), via `tools/legacy_extract_rank.py --current`.
- `score_overrides.csv` — one row, added by hand: Renaissance Park vs Bentwinds (7/5/2023) has no
  score in the dataclip or the Results sheet; the workbook standings credit both with a tie.
- The 2023/2024 dataclips use SwimTopia's long club names ("Abbington Alligators"); see `aliases`
  in `config.yaml`. TSA Champs / Cary City rows are ignored (not dual meets).

## Run
- Date: 2026-10-17
- Code version (commit): see `git log -- data/2023/output`
- Command: `python src/scheduling.py data/2023 --compare data/2024/input`
- Weights: copied from `data/2026/config.yaml` (tuned on 2026 only — this season is out-of-sample).
- Result vs committee's approved 2024 ranks: North 13/38 exact (26 within 1, max off 5),
  South 17/50 exact (41 within 1, max off 3). Weakest of the four seasons; the one large miss
  is Black Horse Run (committee 25, engine 20).
  Full breakdown in `output/ranking_report.csv` and [docs/accuracy_summary.md](../../docs/accuracy_summary.md).
