# Data Formats

## Ranks CSV (`north_ranks.csv`, `south_ranks.csv`)

Both the engine's **input** (rank entering the season) and its **output**
(proposed rank for next season) use this format, so one season's output is
the next season's input unchanged.

```
rank,team
1,Seven Oaks
2,University Club
```

Ranks are contiguous `1..N`; team names are the canonical names every other
file is mapped onto (see `aliases` in `config.yaml`). A ranked team that swims
no meets is dropped and the league renumbered; a team that swims but is not
ranked must be declared in `new_teams` and is appended at the bottom.

## Score overrides CSV (`score_overrides.csv`)

Optional. Corrections the league applied to dataclip scores, typically
rain-shortened meets that never reached official status and are recorded as a
1-1 tie (or 1-0 if one team is awarded the win).

```
date,team_a,team_b,score_a,score_b,note
7/7/2026,Cary,Scottish Hills,1,1,incomplete meet recorded as official result tie
```

Team order within a row does not matter; the pair is matched to the dataclip
meet. Overridden meets count as W/L/T normally but contribute ~0 point
differential.

## Ranking report CSV (`output/ranking_report.csv`)

One row per team, sorted by league then new rank. Columns: `league, new_rank,
prev_rank, change, team, prev_division, div_record, ovr_record, div_pd,
ovr_pd, div_winner, div_loser, travel_miles, travel_minutes, rating,
c_<weight>...` (one column per weight in `config.yaml`, the points it
contributed) and `adjustments` (`|`-separated log of HTH/COPD swaps).

## SwimTopia dataclips CSV

File: `<year> TSA MEET RESULTS - SWIMTOPIA DATACLIPS.csv`

One row per dual meet. Columns:

| Column | Description |
|---|---|
| `meet_date` | `M/D/YYYY` |
| `meet_name` | e.g. `2026 Medfield Pool at Alligators`; `BYE` for bye weeks |
| `team1_abbrev`, `team1_name` | First team |
| `team1_is_home` | `TRUE`/`FALSE` |
| `team1_score`, `team1_place` | Score and finishing place (1 or 2) |
| `team1_win_count`, `team1_loss_count`, `team1_tie_count` | Running record |
| `team2_*` | Same fields for the second team |
| `DIFFERENTIAL` | `team1_score - team2_score` |

Quirks the loader handles: `BYE` rows (one team, no opponent), blank
separator rows between weeks with a stray `DIFFERENTIAL` subtotal, and
float-typed scores (half points exist). Scores are as recorded when the meet
ended; use `score_overrides.csv` for league rulings.

## Team addresses / distance matrices

- `team_addresses.csv`: `division, team, url, address, latitude, longitude, note`
  (from `tools/scrape_team_addresses.py`).
- `team_distances.csv`, `team_drive_minutes.csv`: square matrices, first row
  and first column are team names, diagonal 0, values in road miles (1
  decimal) / whole minutes (from `tools/build_team_distances.py`).

Club names on these come from the TSA website and may need `aliases` to match
the ranks CSVs (e.g. `Lakepark` → `Lake Park`).

## Dual Meet Summary workbook (legacy)

File: `<year> Dual Meet Summary v.X.Y ... .xlsx`

Maintained by hand by the L&S chair through 2026. The engine does not read
it; two tools extract what we need (`legacy_extract_rank.py` → ranks CSVs from
the `* Report` sheets, `legacy_extract_score_overrides.py` → overrides from
`Results`). Sheets present in every year:

| Sheet | Purpose |
|---|---|
| `South`, `North` | Division grids: meet-by-meet results per team |
| `Results` | Flat list of all dual meet results (~275 rows) |
| `Visuals`, `Visual-South` | Chart source data |
| `South Report`, `North Report` | Formatted division reports |
| `South Standings`, `North Standings` | End-of-season standings / rankings |
| `Notes` | Free-form notes |
| `Entry` | Data entry sheet (print area is `Entry!A:E`) |
| `Version Control` | Change log (v3.0+ only) |

Some years add duplicate sheets like `South Report (2)`; treat the unsuffixed
sheet as canonical.

## Reading the files in Python

```python
import pandas as pd

results = pd.read_csv("data/2026/input/2026 TSA MEET RESULTS - SWIMTOPIA DATACLIPS.csv")
standings = pd.read_excel(
    "data/2026/input/2025 Dual Meet Summary v.3.0 - MN Copy.xlsx",
    sheet_name=["South Standings", "North Standings"],
)
```

`openpyxl` emits a harmless `UserWarning` about the `Entry` print area; it
can be ignored.
