# TSA Scheduler

Scheduling tools for the Tarheel Swim Association (TSA).

## Layout

- `src/` – scheduler code (year-agnostic; takes a year/config as input)
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

To compute year **N** you need two inputs in `data/N/input/`:

1. `<N-1> Dual Meet Summary ... .xlsx` – the **previous** season's summary
   workbook, which supplies team rankings/standings.
2. `<N> TSA MEET RESULTS - SWIMTOPIA DATACLIPS.csv` – the current season's
   meet results exported from SwimTopia.

Note the one-year offset: the 2026 run uses the 2025 workbook. The newest
workbook (e.g. 2026) therefore lives in `data/2027/input/`, ready for next
season.

See [docs/data-formats.md](docs/data-formats.md) for column/sheet details.

### Extracting rankings from the legacy workbook

The scheduler does not read the xlsx directly. Instead, run
`src/legacy_extract_rank.py` once per season to pull the hand-calculated
"proposed next-season rank" out of the workbook's `North Report` and
`South Report` sheets into two small CSVs:

```bash
source .venv/bin/activate
python src/legacy_extract_rank.py "data/2027/input/2026 Dual Meet Summary v.4.0 - MN Copy.xlsx"
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

Details:

- The CSVs are written next to the workbook by default; use `--out-dir` to
  override.
- The script **requires** both `North Report` and `South Report` sheets and
  exits non-zero if either is missing.
- It reads column A (rank) and column B (team) starting at row 4, skips the
  `**Any New Teams to be added here…` placeholder row, and validates that
  ranks are contiguous `1..N` with no duplicate team names.
- A workbook whose Report sheets are unfilled (e.g. the 2022 file, which is
  all `#N/A`) is rejected rather than producing an empty CSV.
- Commit the generated CSVs alongside the workbook — they are the canonical
  input for the scheduler; the xlsx is kept for provenance only.

## Running a season

1. Create `data/<year>/` (copy an existing year's folder as a template).
2. Drop the two input files into `data/<year>/input/` and fill in `config.yaml`.
3. Run `src/legacy_extract_rank.py` on the workbook to produce
   `north_ranks.csv` / `south_ranks.csv` (see above).
4. Run the scheduler pointing at that year.
5. Fill in `data/<year>/README.md` with run date and commit hash.
6. Commit inputs, config, and outputs together.
