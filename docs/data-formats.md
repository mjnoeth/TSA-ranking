# Input Data Formats

## SwimTopia dataclips CSV

File: `<year> TSA MEET RESULTS - SWIMTOPIA DATACLIPS.csv`

One row per dual meet. Columns:

| Column | Description |
|---|---|
| `meet_date` | `M/D/YYYY` |
| `meet_name` | e.g. `2026 Medfield Pool at Alligators` |
| `team1_abbrev`, `team1_name` | First team |
| `team1_is_home` | `TRUE`/`FALSE` |
| `team1_score`, `team1_place` | Score and finishing place (1 or 2) |
| `team1_win_count`, `team1_loss_count`, `team1_tie_count` | Running record |
| `team2_*` | Same fields for the second team |
| `DIFFERENTIAL` | `team1_score - team2_score` |

## Dual Meet Summary workbook

File: `<year> Dual Meet Summary v.X.Y ... .xlsx`

Maintained by hand each season; the version in `data/N/input/` is the
workbook from season N-1 and is used for rankings. Sheets present in every
year:

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
