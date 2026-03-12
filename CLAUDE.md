# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

This repository tracks football match data for a team. It stores raw Dribl exports (XLSX snapshots), coach-entered notes, and generates normalized processed datasets via Python + GitHub Actions.

## Commands

**Install dependencies:**
```bash
pip install -r requirements.txt
```

**Convert the latest Dribl snapshot to CSV (run from repo root):**
```bash
python scripts/dribl_matches_export_to_csv.py
```

**Convert a specific snapshot:**
```bash
python scripts/dribl_matches_export_to_csv.py --input data/raw/dribl/matches_YYYY-MM-DD.xlsx
```

**Write to a custom output path:**
```bash
python scripts/dribl_matches_export_to_csv.py --output path/to/output.csv
```

## Architecture

### Data flow

1. **Raw snapshots** — Dribl XLSX exports saved to `data/raw/dribl/matches_YYYY-MM-DD.xlsx` (never edited in place).
2. **Converter script** — `scripts/dribl_matches_export_to_csv.py` reads the latest snapshot (by date in filename, falling back to mtime), renames columns to snake_case, normalizes date/duration/score types, sorts rows, and writes `data/processed/matches.csv`.
3. **Coach notes** — `notes/match_notes.csv` (one row per fixture) and `notes/match_tags.csv` (multiple rows per fixture) are manually maintained and keyed by `fixture_id`.

### Primary key

`fixture_id` (the Dribl `Identifier` column) is the join key across all datasets.

### GitHub Actions workflows

- **`validate-dribl-snapshots_Version2.yml`** — Runs on PRs/pushes when XLSX files change. Enforces filename pattern `matches_YYYY-MM-DD.xlsx` and max size of 5 MiB.
- **`build-matches-csv_Version2.yml`** — Runs on push to `main` when XLSX/script/requirements change. Auto-commits updated `data/processed/matches.csv`.
- **`check-matches-csv-up-to-date_Version2.yml`** — Runs on PRs. Fails if `data/processed/matches.csv` doesn't match what the script would generate. **Always commit the regenerated CSV before opening a PR.**

### Workflow for adding a new match export

1. Save Dribl export as `data/raw/dribl/matches_YYYY-MM-DD.xlsx`.
2. Run `python scripts/dribl_matches_export_to_csv.py`.
3. Commit both the new XLSX snapshot and the updated `data/processed/matches.csv`.
4. Open a PR — recommended branch name: `add-dribl-snapshot-YYYY-MM-DD`.

## Data conventions

- Snapshot filenames **must** match `matches_YYYY-MM-DD.xlsx` (enforced by CI).
- `data/processed/matches.csv` is machine-generated — always regenerate via the script, never edit manually.
- Coach notes use `;` to separate multiple items in free-text fields.
- Tags in `notes/match_tags.csv` use `lower_snake_case` (e.g., `conceded_set_piece`, `press_successful`).
