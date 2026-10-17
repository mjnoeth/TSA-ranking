# TSA Scheduler

Dual-meet scheduler for the Tarheel Swim Association (TSA).

## Layout

- `src/` – scheduler code (year-agnostic; takes a year/config as input)
  - `src/tools/` – one-off helper scripts for preparing input data (see
    [Tools](#tools) below); not part of the scheduler itself
- `tests/` – automated tests
- `docs/` – rules, design notes, how-to-run
  - [docs/data-formats.md](docs/data-formats.md) – what the input files contain
- `config/` – shared default settings and templates for per-year configs
- `data/<year>/` – one folder per season
  - `README.md` – where the inputs came from, when the run was done
  - `config.yaml` – year-specific settings
  - `input/` – source data for that season
  - `output/` – generated schedules and reports

## Setup

Python 3.12+ is required. Create a virtual environment and install dependencies:

```bash
# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

```powershell
# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

The `.venv/` directory is ignored by git; `requirements.txt` is the source of
truth for dependencies. If you add a package, add it there too.

## Inputs for a season

To schedule year **N**, `data/N/input/` holds:

| File | Source | Purpose |
|---|---|---|
| `north_ranks.csv`, `south_ranks.csv` | `tools/legacy_extract_rank.py` run on the **N-1** workbook | Team rank order per league (`rank,team`) |
| `team_addresses.csv` | `tools/scrape_team_addresses.py` | Pool address + lat/long per club |
| `<N> TSA MEET RESULTS - SWIMTOPIA DATACLIPS.csv` | SwimTopia export | Current-season meet results |
| `<N-1> Dual Meet Summary ... .xlsx` | League spreadsheet | Provenance only — the scheduler reads the CSVs, not the workbook |

Note the one-year offset: the 2026 season uses rankings produced at the end of
2025. The newest workbook (e.g. 2026) therefore lives in `data/2027/input/`,
ready for next season.

The CSVs are the canonical scheduler inputs; commit them alongside the raw
sources. See [docs/data-formats.md](docs/data-formats.md) for column/sheet
details.

## Running a season

1. Create `data/<year>/` (copy an existing year's folder as a template).
2. Drop the SwimTopia CSV and prior-year workbook into `data/<year>/input/`
   and fill in `config.yaml`.
3. Generate `north_ranks.csv` / `south_ranks.csv` and `team_addresses.csv`
   using the tools below.
4. Run the scheduler pointing at that year.
5. Fill in `data/<year>/README.md` with run date and commit hash.
6. Commit inputs, config, and outputs together.

## Tools

Helper scripts in `src/tools/` prepare scheduler inputs. They are run once per
season and are independent of the scheduler.

### `legacy_extract_rank.py` — rankings from the legacy workbook

Pulls the hand-calculated "proposed next-season rank" out of the workbook's
`North Report` and `South Report` sheets into two CSVs:

```bash
python src/tools/legacy_extract_rank.py "data/2027/input/2026 Dual Meet Summary v.4.0 - MN Copy.xlsx"
# North Report: 37 teams -> data/2027/input/north_ranks.csv
# South Report: 51 teams -> data/2027/input/south_ranks.csv
```

Output format (`rank,team`, sorted by rank):

```
rank,team
1,Seven Oaks
2,University Club
...
```

- CSVs are written next to the workbook by default; `--out-dir` overrides.
- **Requires** both `North Report` and `South Report` sheets; exits non-zero
  if either is missing.
- Reads column A (rank) and column B (team) from row 4, skips the
  `**Any New Teams to be added here…` placeholder, and validates that ranks
  are contiguous `1..N` with no duplicate names.
- A workbook whose Report sheets are unfilled (e.g. the 2022 file, all
  `#N/A`) is rejected rather than producing an empty CSV.

### `scrape_team_addresses.py` — club addresses from SwimTopia

Scrapes the TSA SwimTopia roster page and each club page for the pool
address and lat/long:

```bash
python src/tools/scrape_team_addresses.py --out data/2026/input/team_addresses.csv
```

Output columns: `division, team, url, address, latitude, longitude, note`.
Addresses come from the Google Maps snippet on each club page; a club with no
map snippet falls back to the address text on the page and is flagged in
`note` (currently only Preston Village, which therefore has no lat/long).

Club names on the website differ slightly from the Dual Meet Summary in a few
cases (e.g. `Lakepark` vs `Lake Park`, `Brier Creek Country Club` vs
`Brier Creek`), so joining to `*_ranks.csv` needs a small alias map.
