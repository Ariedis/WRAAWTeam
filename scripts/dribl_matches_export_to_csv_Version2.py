from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd


RAW_DIR = Path("data/raw/dribl")
OUT_PATH = Path("data/processed/matches.csv")

COLUMN_MAP = {
    "Identifier": "fixture_id",
    "Event Status": "event_status",
    "Matchsheet Status": "matchsheet_status",
    "Competition": "competition",
    "Round": "round",
    "Date": "date",
    "Day": "day",
    "Start": "start_time",
    "Duration": "duration_min",
    "Ground": "ground",
    "Field": "field",
    "League": "league",
    "Age Group": "age_group",
    "Division": "division",
    "Gender": "gender",
    "Home Club Code": "home_club_code",
    "Home Club Name": "home_club_name",
    "Home Team Code": "home_team_code",
    "Home Team Group": "home_team_group",
    "Home Team": "home_team",
    "Away Club Code": "away_club_code",
    "Away Club Name": "away_club_name",
    "Away Team Code": "away_team_code",
    "Away Team Group": "away_team_group",
    "Away Team": "away_team",
    "Home Score": "home_score",
    "Away Score": "away_score",
    "Home Extra Time Score": "home_extra_time_score",
    "Away Extra Time Score": "away_extra_time_score",
    "Home Penalty Score": "home_penalty_score",
    "Away Penalty Score": "away_penalty_score",
    "Status": "status",
}

DATE_SNAPSHOT_RE = re.compile(r"^matches_(\d{4}-\d{2}-\d{2})\.xlsx$", re.IGNORECASE)
DURATION_MIN_RE = re.compile(r"^\s*(\d+)\s*min\s*$", re.IGNORECASE)


@dataclass(frozen=True)
class Snapshot:
    path: Path
    snapshot_date: Optional[datetime]


def find_latest_snapshot(raw_dir: Path) -> Path:
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw directory not found: {raw_dir}")

    candidates: list[Snapshot] = []
    for p in raw_dir.glob("matches_*.xlsx"):
        m = DATE_SNAPSHOT_RE.match(p.name)
        snap_dt = None
        if m:
            snap_dt = datetime.strptime(m.group(1), "%Y-%m-%d")
        candidates.append(Snapshot(path=p, snapshot_date=snap_dt))

    if not candidates:
        raise FileNotFoundError(f"No snapshot files found in {raw_dir} (expected matches_YYYY-MM-DD.xlsx)")

    dated = [c for c in candidates if c.snapshot_date is not None]
    if dated:
        return max(dated, key=lambda c: c.snapshot_date).path

    return max(candidates, key=lambda c: c.path.stat().st_mtime).path


def parse_duration_to_min(val) -> Optional[int]:
    if pd.isna(val):
        return None
    s = str(val).strip()
    if not s:
        return None
    m = DURATION_MIN_RE.match(s)
    if m:
        return int(m.group(1))
    try:
        return int(float(s))
    except ValueError:
        raise ValueError(f"Unrecognized duration format: {val!r} (expected like '100 min')")


def coerce_int_series(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").astype("Int64")


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert Dribl match export snapshots to a normalized CSV.")
    parser.add_argument("--input", type=str, default="", help="Optional path to a specific matches_YYYY-MM-DD.xlsx file.")
    parser.add_argument("--output", type=str, default=str(OUT_PATH), help="Output CSV path.")
    args = parser.parse_args()

    in_path = Path(args.input) if args.input else find_latest_snapshot(RAW_DIR)
    out_path = Path(args.output)

    df = pd.read_excel(in_path, engine="openpyxl")

    missing = [c for c in COLUMN_MAP.keys() if c not in df.columns]
    if missing:
        raise KeyError(f"Input is missing expected columns: {missing}")

    df = df.rename(columns=COLUMN_MAP)

    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    if df["date"].isna().any():
        raise ValueError("Failed to parse one or more dates.")

    df["start_time"] = df["start_time"].astype(str).str.strip()

    df["duration_min"] = df["duration_min"].apply(parse_duration_to_min).astype("Int64")

    for col in [
        "home_score",
        "away_score",
        "home_extra_time_score",
        "away_extra_time_score",
        "home_penalty_score",
        "away_penalty_score",
    ]:
        df[col] = coerce_int_series(df[col])

    sort_cols = [c for c in ["date", "start_time", "competition", "round", "fixture_id"] if c in df.columns]
    df = df.sort_values(sort_cols).reset_index(drop=True)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)

    print(f"Wrote {len(df)} rows to {out_path} from {in_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())