# TSA Scheduler

Scheduling tools for the Tarheel Swim Association (TSA).

## Layout

- `src/` – scheduler code (year-agnostic; takes a year/config as input)
- `tests/` – automated tests
- `docs/` – rules, design notes, how-to-run
- `config/` – shared default settings and templates for per-year configs
- `data/<year>/` – one folder per season
  - `README.md` – where the inputs came from, when the run was done
  - `config.yaml` – year-specific settings
  - `input/` – source data for that season
  - `output/` – generated schedules and reports

## Running a season

1. Create `data/<year>/`, copy in inputs and a `config.yaml`.
2. Run the scheduler pointing at that year.
3. Commit inputs, config, and outputs together.
