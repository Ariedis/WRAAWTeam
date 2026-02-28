# WRAAWTeam Repository Guide

This repository stores fixtures/results exports from Dribl and coach-entered notes so we can produce consistent, repeatable match/training reports and simple analytics.

## Goals

- Keep **raw exports** from Dribl intact and traceable (snapshots).
- Maintain small, structured **coach notes** that are easy to analyze.
- Generate **processed** datasets and **reports** via Python scripts + GitHub Actions.
- Use GitHub Pull Requests + checks to keep data and outputs consistent.

---

## Expected repository structure

```
.
├─ README.md
├─ requirements.txt
├─ scripts/
│  └─ dribl_matches_export_to_csv.py
├─ data/
│  ├─ raw/
│  │  └─ dribl/
│  │     └─ matches_YYYY-MM-DD.xlsx
│  ├─ processed/
│  │  └─ matches.csv
│  └─ README.md
├─ notes/
│  ├─ match_notes.csv
│  └─ match_tags.csv
├─ reports/
│  └─ weekly/
└─ .github/
   └─ workflows/
      ├─ validate-dribl-snapshots.yml
      └─ check-matches-csv-up-to-date.yml
```

### Folder purposes

- `data/raw/dribl/`  
  Raw Dribl exports (XLSX) saved as **snapshots**. These files are never edited in place.

- `data/processed/`  
  Machine-generated, normalized datasets that scripts and reports read from.

- `notes/`  
  Coach-entered notes and tags keyed by `fixture_id` (Dribl `Identifier`). This is the main place to capture information from the PDF match sheet and your observations.

- `reports/weekly/`  
  Generated outputs (future). Keep these as derived artifacts.

---

## Data conventions

### Primary key / joins
- `fixture_id` is the **canonical key** everywhere.
- `fixture_id` is the Dribl `Identifier` from the export.

### Dribl snapshot file naming (required)
Save Dribl match exports under:

- `data/raw/dribl/matches_YYYY-MM-DD.xlsx`

Example:
- `data/raw/dribl/matches_2026-02-28.xlsx`

This naming is enforced by GitHub Actions.

### Normalized match export schema
`data/processed/matches.csv` is generated from the latest snapshot and uses snake_case column names.

Examples:
- `fixture_id`
- `date` (YYYY-MM-DD)
- `start_time` (HH:MM)
- `duration_min` (integer minutes)
- `home_team`, `away_team`, `home_score`, `away_score`, etc.

---

## Coach notes (manual inputs)

### `notes/match_notes.csv` (one row per fixture)
Recommended columns:

- `fixture_id`
- `formation` (e.g., `4-3-3`)
- `key_themes_for` (free text)
- `key_themes_against` (free text)
- `focus_next_week` (free text)

Guidelines:
- Keep each theme concise (bullets separated by `;` is fine).
- Prefer actionable observations: “struggled to play through central press” > “midfield bad”.

### `notes/match_tags.csv` (multiple rows per fixture, optional)
Recommended columns:

- `fixture_id`
- `tag`
- `count` (optional; defaults to 1)

Suggested tag style:
- Use lower_snake_case tags, e.g.
  - `conceded_set_piece`
  - `conceded_through_ball`
  - `lost_ball_central`
  - `created_chances_right`
  - `press_successful`
  - `build_out_issues`

Tags make it easy to summarize trends over 3–5 matches.

---

## Workflow: adding a new match export

1. Export matches from Dribl to XLSX.
2. Save as a snapshot:
   - `data/raw/dribl/matches_YYYY-MM-DD.xlsx`
3. Run the converter locally:
   - `python scripts/dribl_matches_export_to_csv.py`
4. Commit:
   - the new snapshot XLSX
   - the updated `data/processed/matches.csv`
5. Open a Pull Request into `main`.

### Why `matches.csv` must be committed
A PR check will fail if the generated `data/processed/matches.csv` differs from what the script would generate. This keeps processed data consistent and viewable directly in GitHub.

---

## GitHub Actions checks

### 1) Validate Dribl snapshots
Workflow: `Validate Dribl XLSX snapshots`

- Enforces filename pattern: `matches_YYYY-MM-DD.xlsx`
- Enforces max file size threshold (currently 5 MiB)

### 2) Check `matches.csv` is up to date
Workflow: `Check matches.csv is up to date`

- Re-runs the converter in CI
- Fails the PR if the generated `data/processed/matches.csv` differs

---

## Branching and PR practices (solo)

- Use PRs for changes to:
  - `data/raw/dribl/*.xlsx`
  - scripts and workflows
  - notes and reports
- Keep `main` protected with required status checks.

Recommended branch naming:
- `add-dribl-snapshot-2026-03-07`
- `update-converter`
- `add-match-notes-round-2`

---

## Suggested Copilot usage (“agents” / roles)

Even as a solo maintainer, it helps to use Copilot with clear roles and constraints. Below are suggested “agents” you can prompt for.

### Agent: Data Steward
Use for:
- Designing CSV schemas and data dictionaries
- Validating column types and naming conventions
- Adding checks (missing values, duplicate fixture_id)

Prompt examples:
- “Review this CSV schema and suggest improvements for consistency and future analytics.”
- “Suggest validations to ensure fixture_id is unique and scores are numeric when status is Complete.”

### Agent: Automation Engineer
Use for:
- Writing/modifying GitHub Actions workflows
- Ensuring PR checks are fast and reliable
- Preventing workflow loops and keeping diffs stable

Prompt examples:
- “Update this workflow so it runs only on relevant paths and provides clear failure messages.”
- “Add a check that warns if a snapshot file is missing the expected columns.”

### Agent: Analyst (Football / Training)
Use for:
- Turning match notes/tags into training priorities
- Building simple metrics (form, trends, set-piece tracking)
- Producing a weekly report outline

Prompt examples:
- “Given these match tags for the last 3 fixtures, propose next week’s training priorities.”
- “Design a weekly report template that’s actionable for session planning.”

### Agent: Documentation Editor
Use for:
- Improving clarity of README/docs
- Creating templates for match notes and weekly planning

Prompt examples:
- “Rewrite this section to be clearer and more concise for future maintenance.”
- “Create a match report template that fits in a CSV note field plus tags.”

### Guardrails for Copilot content
- Treat Copilot output as a draft; keep the coach’s judgement as the final decision-maker.
- Do not store sensitive medical data here (by design).
- Prefer consistent, structured data (IDs + tags) over long unstructured text when possible.

---

## Future (optional) enhancements

- Weekly report generator script:
  - `scripts/build_weekly_report.py` → `reports/weekly/YYYY-MM-DD.md`
- Add a `data/README.md` data dictionary with:
  - column definitions
  - units (minutes, scores)
  - allowed values for tags