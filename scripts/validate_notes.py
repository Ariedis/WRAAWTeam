"""Cross-validate coach notes against matches.csv.

Checks:
1. Every fixture_id in match_notes.csv and match_tags.csv exists in matches.csv.
2. Every tag in match_tags.csv is in the approved tag dictionary (docs/tag-dictionary.md).
3. Warns if completed fixtures older than 30 days are missing notes.
4. Validates players.csv (positions, active flag, duplicate IDs).
5. Validates attendance.csv (session_type, player IDs, status, fixture linkage).
6. Validates lineups.csv (fixture completeness, position codes, player IDs).

Exits with code 1 if any errors are found; warnings are printed but do not fail.
"""
from __future__ import annotations

import re
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

MATCHES_PATH    = Path("data/processed/matches.csv")
NOTES_PATH      = Path("notes/match_notes.csv")
TAGS_PATH       = Path("notes/match_tags.csv")
TAG_DICT_PATH   = Path("docs/tag-dictionary.md")
PLAYERS_PATH    = Path("notes/players.csv")
ATTENDANCE_PATH = Path("notes/attendance.csv")
LINEUPS_PATH    = Path("notes/lineups.csv")
POSITIONS_PATH  = Path("docs/positions.md")

MISSING_NOTES_THRESHOLD_DAYS = 30


def load_approved_tags(tag_dict_path: Path) -> set[str]:
    """Extract tag names from the tag dictionary Markdown table rows."""
    if not tag_dict_path.exists():
        return set()
    text = tag_dict_path.read_text(encoding="utf-8")
    # Match backtick-quoted tags in table cells: | `tag_name` |
    return set(re.findall(r"`([a-z][a-z0-9_]*)`", text))


def load_approved_positions(path: Path) -> set[str]:
    """Extract 2-5 uppercase-letter position codes from positions.md table rows."""
    if not path.exists():
        return set()
    return set(re.findall(r"\|\s+([A-Z]{2,5})\s+\|", path.read_text(encoding="utf-8")))


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    # --- Load matches ---
    if not MATCHES_PATH.exists():
        errors.append(f"matches.csv not found at {MATCHES_PATH}")
        print("\n".join(f"ERROR: {e}" for e in errors))
        return 1

    matches = pd.read_csv(MATCHES_PATH)
    matches["date"] = pd.to_datetime(matches["date"], errors="coerce")
    valid_ids: set[str] = set(matches["fixture_id"].dropna().astype(str))

    # --- Load notes ---
    notes_ids: set[str] = set()
    if NOTES_PATH.exists():
        notes = pd.read_csv(NOTES_PATH)
        if not notes.empty and "fixture_id" in notes.columns:
            notes_ids = set(notes["fixture_id"].dropna().astype(str))
            bad = notes_ids - valid_ids
            for fid in sorted(bad):
                errors.append(
                    f"match_notes.csv: fixture_id '{fid}' not found in matches.csv"
                )

    # --- Load tags ---
    if TAGS_PATH.exists():
        tags = pd.read_csv(TAGS_PATH)
        if not tags.empty and "fixture_id" in tags.columns:
            bad_ids = set(tags["fixture_id"].dropna().astype(str)) - valid_ids
            for fid in sorted(bad_ids):
                errors.append(
                    f"match_tags.csv: fixture_id '{fid}' not found in matches.csv"
                )

        if not tags.empty and "tag" in tags.columns:
            approved = load_approved_tags(TAG_DICT_PATH)
            if approved:
                used_tags = set(tags["tag"].dropna().astype(str))
                unknown = used_tags - approved
                for tag in sorted(unknown):
                    errors.append(
                        f"match_tags.csv: tag '{tag}' is not in the approved tag dictionary "
                        f"(docs/tag-dictionary.md)"
                    )

    # --- Validate players.csv ---
    valid_player_ids: set[str] = set()
    if PLAYERS_PATH.exists():
        players = pd.read_csv(PLAYERS_PATH)
        if not players.empty and "player_id" in players.columns:
            approved_positions = load_approved_positions(POSITIONS_PATH)
            # Duplicate player_id
            dupes = players[players.duplicated("player_id", keep=False)]["player_id"].unique()
            for pid in sorted(str(p) for p in dupes):
                errors.append(f"players.csv: duplicate player_id '{pid}'")
            valid_player_ids = set(players["player_id"].dropna().astype(str))
            # primary_position
            if "primary_position" in players.columns and approved_positions:
                for _, row in players.iterrows():
                    pos = str(row["primary_position"]) if pd.notna(row.get("primary_position")) else ""
                    if pos and pos not in approved_positions:
                        errors.append(
                            f"players.csv: player_id '{row['player_id']}' has unknown "
                            f"primary_position '{pos}'"
                        )
            # preferred_positions
            if "preferred_positions" in players.columns and approved_positions:
                for _, row in players.iterrows():
                    prefs = str(row["preferred_positions"]) if pd.notna(row.get("preferred_positions")) else ""
                    for code in [p.strip() for p in prefs.split(";") if p.strip()]:
                        if code not in approved_positions:
                            errors.append(
                                f"players.csv: player_id '{row['player_id']}' has unknown "
                                f"preferred_position '{code}'"
                            )
            # active flag
            if "active" in players.columns:
                for _, row in players.iterrows():
                    val = str(row["active"]).strip().upper() if pd.notna(row.get("active")) else ""
                    if val not in ("TRUE", "FALSE", ""):
                        errors.append(
                            f"players.csv: player_id '{row['player_id']}' has invalid "
                            f"active value '{row['active']}' (must be TRUE or FALSE)"
                        )

    # --- Validate attendance.csv ---
    if ATTENDANCE_PATH.exists():
        attendance = pd.read_csv(ATTENDANCE_PATH)
        if not attendance.empty:
            today = date.today()
            for i, row in attendance.iterrows():
                pid = str(row.get("player_id", "")).strip()
                stype = str(row.get("session_type", "")).strip().lower()
                fid = str(row.get("fixture_id", "")).strip()
                status = str(row.get("status", "")).strip().lower()
                sdate_raw = str(row.get("session_date", "")).strip()

                if stype not in ("game", "training"):
                    errors.append(
                        f"attendance.csv row {i + 2}: session_type '{stype}' "
                        f"must be 'game' or 'training'"
                    )
                if valid_player_ids and pid not in valid_player_ids:
                    errors.append(
                        f"attendance.csv row {i + 2}: player_id '{pid}' "
                        f"not found in players.csv"
                    )
                if status not in ("present", "absent", "unavailable"):
                    errors.append(
                        f"attendance.csv row {i + 2}: status '{status}' "
                        f"must be 'present', 'absent', or 'unavailable'"
                    )
                if stype == "game":
                    if not fid or fid == "nan":
                        errors.append(
                            f"attendance.csv row {i + 2}: fixture_id required for game rows"
                        )
                    elif fid not in valid_ids:
                        errors.append(
                            f"attendance.csv row {i + 2}: fixture_id '{fid}' "
                            f"not found in matches.csv"
                        )
                elif stype == "training":
                    if fid and fid != "nan":
                        errors.append(
                            f"attendance.csv row {i + 2}: fixture_id must be empty for training rows"
                        )
                # Warn if unavailable used for a past date
                if status == "unavailable" and sdate_raw and sdate_raw != "nan":
                    try:
                        sdate = date.fromisoformat(sdate_raw)
                        if sdate < today:
                            warnings.append(
                                f"attendance.csv row {i + 2}: status 'unavailable' used for "
                                f"past date {sdate_raw} (use 'absent' for retrospective records)"
                            )
                    except ValueError:
                        pass

    # --- Validate lineups.csv ---
    if LINEUPS_PATH.exists():
        lineups = pd.read_csv(LINEUPS_PATH)
        if not lineups.empty:
            approved_positions = load_approved_positions(POSITIONS_PATH)
            # Build set of completed fixture IDs
            completed_ids: set[str] = set(
                matches[matches["event_status"].str.lower().eq("complete")]["fixture_id"]
                .dropna().astype(str)
            )
            # Track player appearances per fixture for duplicate warning
            fixture_player_slots: dict[str, list[str]] = {}
            for i, row in lineups.iterrows():
                fid = str(row.get("fixture_id", "")).strip()
                slot = str(row.get("position_slot", "")).strip()
                pid = str(row.get("player_id", "")).strip()

                if fid not in valid_ids:
                    errors.append(
                        f"lineups.csv row {i + 2}: fixture_id '{fid}' "
                        f"not found in matches.csv"
                    )
                elif fid in completed_ids:
                    errors.append(
                        f"lineups.csv row {i + 2}: fixture_id '{fid}' "
                        f"belongs to a completed match"
                    )
                if approved_positions and slot not in approved_positions:
                    errors.append(
                        f"lineups.csv row {i + 2}: position_slot '{slot}' "
                        f"is not an approved position code"
                    )
                if pid and pid != "nan":
                    if valid_player_ids and pid not in valid_player_ids:
                        errors.append(
                            f"lineups.csv row {i + 2}: player_id '{pid}' "
                            f"not found in players.csv"
                        )
                    fixture_player_slots.setdefault(fid, []).append(pid)

            # Warn about players in multiple slots for the same fixture
            for fid, pids in fixture_player_slots.items():
                seen: dict[str, int] = {}
                for pid in pids:
                    seen[pid] = seen.get(pid, 0) + 1
                for pid, count in seen.items():
                    if count > 1:
                        warnings.append(
                            f"lineups.csv: player_id '{pid}' appears in {count} slots "
                            f"for fixture '{fid}'"
                        )

    # --- Warn about completed fixtures missing notes ---
    cutoff = date.today() - timedelta(days=MISSING_NOTES_THRESHOLD_DAYS)
    completed = matches[
        matches["event_status"].str.lower().eq("complete")
        & matches["date"].notna()
        & (matches["date"].dt.date <= cutoff)
    ]
    missing_notes = completed[~completed["fixture_id"].astype(str).isin(notes_ids)]
    for _, row in missing_notes.iterrows():
        dt = row["date"].strftime("%Y-%m-%d") if pd.notna(row["date"]) else "?"
        warnings.append(
            f"No notes for completed fixture {row['fixture_id']} ({dt}) — "
            f"older than {MISSING_NOTES_THRESHOLD_DAYS} days"
        )

    # --- Report ---
    for w in warnings:
        print(f"WARNING: {w}")

    for e in errors:
        print(f"ERROR: {e}")

    if errors:
        print(f"\n{len(errors)} error(s) found. Fix them before merging.")
        return 1

    print(f"Notes validation passed. {len(warnings)} warning(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
