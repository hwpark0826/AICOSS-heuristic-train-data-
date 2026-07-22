# MUMUT Training Data Builder

## Purpose

Build approximately 900 human heuristic labels from virtual
scenario-store pairs using the MUMUT master workbook.

See:

- AGENTS.md
- docs/MUMUT_DATA_SPEC.md
- docs/SCENARIO_DISTRIBUTION_POLICY.md
- docs/MVP_DEPLOYMENT.md

## Master workbook

Place the workbook at:

data/master/

## Initial setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt 
pytest
```

## Current scope

The completed human-label export is stored at `data/training/heuristic selection data.csv`. It keeps the factual `store_atmosphere` feature, while future scenario generation and model inputs exclude the removed user `requested_atmosphere_code` preference.

The initial MVP uses the reviewed 30-store roster in `config/mvp_store_roster.csv` and creates 240 virtual assignments, with 80 assignments each for A01/A02/A03. `store_id` is the runtime key; `store_name` is only for human review. If a future master makes an enabled roster store unavailable, run creation fails instead of silently replacing it. It discovers the single workbook in `data/master/`, reads row 4 headers, validates keys and references without hard-coded store or route counts, and creates immutable run snapshots. Missing factual values remain `UNKNOWN`; they are never converted into negative values.

The active local MVP run is `run_007` (5차 master, seed 46). For a shared deployment, use the Supabase central-storage procedure in `docs/MVP_DEPLOYMENT.md` after uploading this run.

Create a new run with an explicit ID and seed. Do not reuse an existing run ID.

```bash
python scripts/create_mvp_run.py --run-id run_007 --seed 46
```

## Local labeling screen

Run `python -m streamlit run app.py`, then open `http://localhost:8501`. By default it reads `data/runs/run_007/` and writes to that run's local SQLite database. With `MUMUT_STORAGE=supabase`, it reads and writes the central Supabase database instead.
