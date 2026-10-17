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

## Running a season

1. Create `data/<year>/` (copy an existing year's folder as a template).
2. Drop the two input files into `data/<year>/input/` and fill in `config.yaml`.
3. Run the scheduler pointing at that year.
4. Fill in `data/<year>/README.md` with run date and commit hash.
5. Commit inputs, config, and outputs together.
