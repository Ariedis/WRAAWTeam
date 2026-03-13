"""Extract last N completed matches and emit structured JSON for training report generation.

Usage:
    python scripts/generate_training_data.py
    python scripts/generate_training_data.py --matches 6 --output reports/.training_data_tmp.json
    python scripts/generate_training_data.py --focus "defensive shape" --reveal
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

# Allow importing sibling script
sys.path.insert(0, str(Path(__file__).parent))
from generate_insights import (
    load_matches,
    load_notes,
    load_tags,
    load_players,
    load_attendance,
    load_lineups,
    load_id_map,
    detect_team,
    played_matches,
    result_for,
    goals_for,
    goals_against,
    opponent_name,
    shorten_team,
    display_id,
)


def build_trend_stats(last_n: "pd.DataFrame", our_team: str) -> dict:
    wins = draws = losses = 0
    gf_total = ga_total = 0
    shutouts_kept = shutouts_conceded = 0
    results_parts = []

    for _, row in last_n.iterrows():
        res = result_for(row, our_team)
        gf = goals_for(row, our_team)
        ga = goals_against(row, our_team)
        if res == "W":
            wins += 1
        elif res == "D":
            draws += 1
        else:
            losses += 1
        gf_total += gf
        ga_total += ga
        if ga == 0:
            shutouts_kept += 1
        if gf == 0:
            shutouts_conceded += 1
        results_parts.append(res)

    n = len(last_n)
    return {
        "wins": wins,
        "draws": draws,
        "losses": losses,
        "gf_total": gf_total,
        "ga_total": ga_total,
        "gf_avg": round(gf_total / n, 2) if n else 0.0,
        "ga_avg": round(ga_total / n, 2) if n else 0.0,
        "results_string": "  ".join(results_parts),
        "shutouts_kept": shutouts_kept,
        "shutouts_conceded": shutouts_conceded,
    }


def build_match_list(last_n: "pd.DataFrame", our_team: str) -> list[dict]:
    matches = []
    for _, row in last_n.iterrows():
        dt = row["date"].strftime("%Y-%m-%d") if hasattr(row["date"], "strftime") else str(row["date"])
        home_is_us = our_team in str(row["home_team"])
        matches.append({
            "fixture_id": str(row["fixture_id"]),
            "date": dt,
            "round": int(row["round"]) if str(row.get("round", "")).replace(".", "").isdigit() else None,
            "opponent": shorten_team(opponent_name(row, our_team)),
            "result": result_for(row, our_team),
            "gf": goals_for(row, our_team),
            "ga": goals_against(row, our_team),
            "home_away": "Home" if home_is_us else "Away",
        })
    return matches


NOTE_CONTENT_COLS = ["formation", "key_themes_for", "key_themes_against", "focus_next_week"]


def check_has_notes(notes: "pd.DataFrame", fixture_ids: list[str]) -> bool:
    if notes.empty:
        return False
    relevant = notes[notes["fixture_id"].astype(str).isin(fixture_ids)]
    if relevant.empty:
        return False
    for col in NOTE_CONTENT_COLS:
        if col in relevant.columns:
            filled = relevant[col].dropna().astype(str).str.strip().replace("", float("nan")).dropna()
            if not filled.empty:
                return True
    return False


def build_notes_list(notes: "pd.DataFrame", fixture_ids: list[str]) -> list[dict]:
    if notes.empty:
        return []
    relevant = notes[notes["fixture_id"].astype(str).isin(fixture_ids)]
    result = []
    for _, row in relevant.iterrows():
        entry = {}
        for col in ["fixture_id"] + NOTE_CONTENT_COLS:
            if col in row.index:
                val = row[col]
                import math
                entry[col] = None if (val != val or (isinstance(val, float) and math.isnan(val))) else str(val).strip() or None
        if any(v for k, v in entry.items() if k != "fixture_id"):
            result.append(entry)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract training data JSON from match history.")
    parser.add_argument("--matches", type=int, default=4, help="Last N matches to analyse (default: 4)")
    parser.add_argument("--output", type=str, default="", help="Write JSON to file (default: stdout)")
    parser.add_argument("--reveal", action="store_true", help="Resolve player IDs to names via secrets/player_id_map.csv")
    parser.add_argument("--focus", type=str, default="", help="Optional focus area string")
    parser.add_argument("--team", type=str, default="", help="Override team name detection")
    args = parser.parse_args()

    df = load_matches()
    notes = load_notes()
    tags = load_tags()
    players = load_players()
    attendance = load_attendance()
    lineups = load_lineups()
    id_map = load_id_map() if args.reveal else {}

    our_team = detect_team(df, args.team or None)
    played = played_matches(df, our_team)
    last_n = played.tail(args.matches)
    fixture_ids = last_n["fixture_id"].astype(str).tolist()

    # has_* flags
    has_notes = check_has_notes(notes, fixture_ids)

    relevant_tags = tags[tags["fixture_id"].astype(str).isin(fixture_ids)] if not tags.empty and "fixture_id" in tags.columns else tags.iloc[0:0]
    has_tags = len(relevant_tags) > 0

    # player_notes: check notes/player_notes.csv if it exists
    player_notes_path = Path("notes/player_notes.csv")
    player_notes_list: list[dict] = []
    has_player_notes = False
    if player_notes_path.exists():
        import pandas as pd
        pn = pd.read_csv(player_notes_path)
        if not pn.empty and "fixture_id" in pn.columns:
            relevant_pn = pn[pn["fixture_id"].astype(str).isin(fixture_ids)]
            has_player_notes = len(relevant_pn) > 0
            if has_player_notes:
                player_notes_list = relevant_pn.to_dict(orient="records")

    relevant_att = attendance[attendance["fixture_id"].astype(str).isin(fixture_ids)] if not attendance.empty and "fixture_id" in attendance.columns else attendance.iloc[0:0]
    has_attendance = len(relevant_att) > 0

    relevant_lineups = lineups[lineups["fixture_id"].astype(str).isin(fixture_ids)] if not lineups.empty and "fixture_id" in lineups.columns else lineups.iloc[0:0]
    has_lineups = len(relevant_lineups) > 0

    trend_stats = build_trend_stats(last_n, our_team)
    matches_list = build_match_list(last_n, our_team)
    notes_list = build_notes_list(notes, fixture_ids)

    tags_list: list[dict] = []
    if has_tags:
        for _, row in relevant_tags.iterrows():
            entry = {k: row[k] for k in relevant_tags.columns}
            tags_list.append(entry)

    payload = {
        "generated": date.today().isoformat(),
        "team": our_team,
        "window": args.matches,
        "focus_area": args.focus.strip() or None,
        "has_notes": has_notes,
        "has_tags": has_tags,
        "has_player_notes": has_player_notes,
        "has_attendance": has_attendance,
        "has_lineups": has_lineups,
        "trend_stats": trend_stats,
        "matches": matches_list,
        "notes": notes_list,
        "tags": tags_list,
        "player_notes": player_notes_list,
        "attendance": {"has_data": has_attendance},
        "lineups": relevant_lineups.to_dict(orient="records") if has_lineups else [],
    }

    json_str = json.dumps(payload, indent=2, default=str)

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json_str, encoding="utf-8")
        print(f"Training data written to {out}", file=sys.stderr)
    else:
        print(json_str)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
