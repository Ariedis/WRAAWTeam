"""Generate a Markdown insights report from match data and coach notes.

Usage:
    python scripts/generate_insights.py
    python scripts/generate_insights.py --output reports/custom.md
    python scripts/generate_insights.py --team "West Ryde Rovers"
"""
from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

import pandas as pd

MATCHES_PATH    = Path("data/processed/matches.csv")
NOTES_PATH      = Path("notes/match_notes.csv")
TAGS_PATH       = Path("notes/match_tags.csv")
PLAYERS_PATH    = Path("notes/players.csv")
ATTENDANCE_PATH = Path("notes/attendance.csv")
LINEUPS_PATH    = Path("notes/lineups.csv")
SECRETS_PATH    = Path("secrets/player_id_map.csv")
REPORTS_DIR     = Path("reports")

OUR_TEAM_CODE = "WRR"  # fallback; auto-detected if possible


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_matches() -> pd.DataFrame:
    df = pd.read_csv(MATCHES_PATH)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    for col in ("home_score", "away_score"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.sort_values("date").reset_index(drop=True)


def load_notes() -> pd.DataFrame:
    df = pd.read_csv(NOTES_PATH)
    return df if not df.empty else pd.DataFrame(columns=df.columns)


def load_tags() -> pd.DataFrame:
    df = pd.read_csv(TAGS_PATH)
    if "count" not in df.columns:
        df["count"] = 1
    df["count"] = pd.to_numeric(df["count"], errors="coerce").fillna(1)
    return df if not df.empty else pd.DataFrame(columns=df.columns)


def load_players() -> pd.DataFrame:
    if not PLAYERS_PATH.exists():
        return pd.DataFrame(columns=["player_id", "squad_number", "primary_position", "preferred_positions", "active"])
    df = pd.read_csv(PLAYERS_PATH)
    if df.empty:
        return df
    if "active" in df.columns:
        df["active"] = df["active"].astype(str).str.strip().str.upper().eq("TRUE")
    df["player_id"] = df["player_id"].astype(str)
    return df


def load_attendance() -> pd.DataFrame:
    if not ATTENDANCE_PATH.exists():
        return pd.DataFrame(columns=["session_date", "session_type", "fixture_id", "player_id", "status"])
    df = pd.read_csv(ATTENDANCE_PATH)
    if df.empty:
        return df
    df["session_date"] = pd.to_datetime(df["session_date"], errors="coerce")
    df["player_id"] = df["player_id"].astype(str)
    return df


def load_lineups() -> pd.DataFrame:
    if not LINEUPS_PATH.exists():
        return pd.DataFrame(columns=["fixture_id", "position_slot", "player_id", "notes"])
    df = pd.read_csv(LINEUPS_PATH)
    if df.empty:
        return df
    df["player_id"] = df["player_id"].astype(str)
    return df


def load_id_map() -> dict[str, str]:
    if not SECRETS_PATH.exists():
        return {}
    df = pd.read_csv(SECRETS_PATH)
    if df.empty or "player_id" not in df.columns or "player_name" not in df.columns:
        return {}
    return {str(row["player_id"]): str(row["player_name"]) for _, row in df.iterrows()}


def display_id(player_id: str, id_map: dict) -> str:
    """Returns real name if id_map has it, else 'Player #<id>'."""
    return id_map.get(str(player_id), f"Player #{player_id}")


def positions_for_player(row) -> set[str]:
    """Returns union of primary_position and preferred_positions codes."""
    positions: set[str] = set()
    if pd.notna(row.get("primary_position")) and str(row["primary_position"]).strip():
        positions.add(str(row["primary_position"]).strip())
    prefs = str(row.get("preferred_positions", "")) if pd.notna(row.get("preferred_positions")) else ""
    for code in [p.strip() for p in prefs.split(";") if p.strip()]:
        positions.add(code)
    return positions


# ---------------------------------------------------------------------------
# Team detection
# ---------------------------------------------------------------------------

def detect_team(df: pd.DataFrame, team_hint: str | None) -> str:
    """Return the display name of our team (appears most often in home+away)."""
    if team_hint:
        return team_hint
    # Find the club_code that appears in most rows
    home_codes = df["home_club_code"].value_counts()
    away_codes = df["away_club_code"].value_counts()
    combined = home_codes.add(away_codes, fill_value=0)
    our_code = combined.idxmax()
    # Grab the full team name for that code
    home_match = df[df["home_club_code"] == our_code]["home_team"].dropna()
    away_match = df[df["away_club_code"] == our_code]["away_team"].dropna()
    names = pd.concat([home_match, away_match])
    return names.mode().iloc[0] if not names.empty else str(our_code)


def is_our_match(row, our_team: str) -> bool:
    return our_team in str(row["home_team"]) or our_team in str(row["away_team"])


def played_matches(df: pd.DataFrame, our_team: str) -> pd.DataFrame:
    mask = (
        df.apply(lambda r: is_our_match(r, our_team), axis=1)
        & df["event_status"].str.lower().eq("complete")
        & df["home_score"].notna()
        & df["away_score"].notna()
    )
    return df[mask].copy()


# ---------------------------------------------------------------------------
# Result helpers
# ---------------------------------------------------------------------------

def result_for(row, our_team: str) -> str:
    """Return 'W', 'L', or 'D' from our team's perspective."""
    home_is_us = our_team in str(row["home_team"])
    our_score = row["home_score"] if home_is_us else row["away_score"]
    opp_score = row["away_score"] if home_is_us else row["home_score"]
    if our_score > opp_score:
        return "W"
    if our_score < opp_score:
        return "L"
    return "D"


def goals_for(row, our_team: str) -> int:
    home_is_us = our_team in str(row["home_team"])
    return int(row["home_score"] if home_is_us else row["away_score"])


def goals_against(row, our_team: str) -> int:
    home_is_us = our_team in str(row["home_team"])
    return int(row["away_score"] if home_is_us else row["home_score"])


def opponent_name(row, our_team: str) -> str:
    if our_team in str(row["home_team"]):
        return str(row["away_team"])
    return str(row["home_team"])


def shorten_team(name: str) -> str:
    """Strip the long suffix for display."""
    # e.g. "North Epping Rangers FC All Age Women's 04 Orange" → "North Epping Rangers FC (Orange)"
    for suffix in [
        " All Age Women's 04 ",
        " All Age Women's 04",
    ]:
        if suffix.strip() in name:
            parts = name.split(suffix.strip())
            base = parts[0].strip()
            group = parts[-1].strip() if len(parts) > 1 else ""
            return f"{base} ({group})" if group else base
    return name


# ---------------------------------------------------------------------------
# Report sections
# ---------------------------------------------------------------------------

def section_season_summary(played: pd.DataFrame, our_team: str) -> str:
    results = played.apply(lambda r: result_for(r, our_team), axis=1)
    gf = played.apply(lambda r: goals_for(r, our_team), axis=1).sum()
    ga = played.apply(lambda r: goals_against(r, our_team), axis=1).sum()
    w = (results == "W").sum()
    d = (results == "D").sum()
    l = (results == "L").sum()
    pts = w * 3 + d
    gd = gf - ga

    lines = [
        "## Season Summary\n",
        f"| Played | W | D | L | GF | GA | GD | Pts |",
        f"|--------|---|---|---|----|----|-----|-----|",
        f"| {len(played)} | {w} | {d} | {l} | {gf} | {ga} | {gd:+d} | {pts} |",
    ]
    return "\n".join(lines)


def section_form(played: pd.DataFrame, our_team: str, n: int = 5) -> str:
    recent = played.tail(n)
    results = recent.apply(lambda r: result_for(r, our_team), axis=1).tolist()
    form_str = "  ".join(results) if results else "—"
    return f"## Recent Form (last {n})\n\n`{form_str}`"


def section_scoring_trend(played: pd.DataFrame, our_team: str) -> str:
    rows = []
    for _, r in played.iterrows():
        dt = r["date"].strftime("%Y-%m-%d") if pd.notna(r["date"]) else "?"
        rnd = int(r["round"]) if pd.notna(r["round"]) else "?"
        gf = goals_for(r, our_team)
        ga = goals_against(r, our_team)
        res = result_for(r, our_team)
        opp = shorten_team(opponent_name(r, our_team))
        rows.append(f"| Rd {rnd} | {dt} | {opp} | {gf} | {ga} | {res} |")

    header = "## Scoring Trend\n\n| Round | Date | Opponent | GF | GA | Result |"
    sep    = "|-------|------|----------|----|----|--------|"
    return "\n".join([header, sep] + rows)


def section_head_to_head(played: pd.DataFrame, our_team: str) -> str:
    records: dict[str, dict] = {}
    for _, r in played.iterrows():
        opp = shorten_team(opponent_name(r, our_team))
        if opp not in records:
            records[opp] = {"W": 0, "D": 0, "L": 0, "GF": 0, "GA": 0}
        res = result_for(r, our_team)
        records[opp][res] += 1
        records[opp]["GF"] += goals_for(r, our_team)
        records[opp]["GA"] += goals_against(r, our_team)

    lines = [
        "## Head-to-Head\n",
        "| Opponent | P | W | D | L | GF | GA | GD |",
        "|----------|---|---|---|---|----|----|-----|",
    ]
    for opp, rec in sorted(records.items()):
        p = rec["W"] + rec["D"] + rec["L"]
        gd = rec["GF"] - rec["GA"]
        lines.append(
            f"| {opp} | {p} | {rec['W']} | {rec['D']} | {rec['L']} "
            f"| {rec['GF']} | {rec['GA']} | {gd:+d} |"
        )
    return "\n".join(lines)


def section_tag_summary(tags: pd.DataFrame, top_n: int = 10) -> str | None:
    if tags.empty or "tag" not in tags.columns:
        return None
    summary = (
        tags.groupby("tag")["count"].sum()
        .sort_values(ascending=False)
        .head(top_n)
    )
    if summary.empty:
        return None
    lines = [
        "## Tag Summary (Top Recurring)\n",
        "| Tag | Total |",
        "|-----|-------|",
    ]
    for tag, count in summary.items():
        lines.append(f"| `{tag}` | {int(count)} |")
    return "\n".join(lines)


def section_next_fixture(df: pd.DataFrame, our_team: str) -> str | None:
    upcoming = df[
        df.apply(lambda r: is_our_match(r, our_team), axis=1)
        & (df["event_status"].str.lower() != "complete")
    ].sort_values("date")
    if upcoming.empty:
        return None
    r = upcoming.iloc[0]
    dt = r["date"].strftime("%A, %d %B %Y") if pd.notna(r["date"]) else "TBC"
    opp = shorten_team(opponent_name(r, our_team))
    venue = r.get("ground", "TBC") or "TBC"
    field = r.get("field", "") or ""
    venue_str = f"{venue}, {field}".strip(", ")
    home_away = "Home" if our_team in str(r.get("home_team", "")) else "Away"
    lines = [
        "## Next Fixture\n",
        f"**{dt}** — Round {int(r['round']) if pd.notna(r.get('round')) else '?'}",
        f"- Opponent: {opp}",
        f"- Venue: {venue_str}",
        f"- {home_away}",
    ]
    return "\n".join(lines)


def section_lineup_status(
    df: pd.DataFrame,
    our_team: str,
    players: pd.DataFrame,
    attendance: pd.DataFrame,
    lineups: pd.DataFrame,
    id_map: dict,
) -> str | None:
    """For each upcoming fixture with lineup rows, show filled/unfilled slots and suggestions."""
    if lineups.empty:
        return None

    today = date.today()
    upcoming = df[
        df.apply(lambda r: is_our_match(r, our_team), axis=1)
        & (df["event_status"].str.lower() != "complete")
    ].sort_values("date")

    if upcoming.empty:
        return None

    # Index unavailable players per fixture
    unavailable_per_fixture: dict[str, set[str]] = {}
    if not attendance.empty and "status" in attendance.columns:
        unav = attendance[attendance["status"].str.lower() == "unavailable"]
        for _, row in unav.iterrows():
            fid = str(row.get("fixture_id", "")).strip()
            pid = str(row.get("player_id", "")).strip()
            if fid and fid != "nan":
                unavailable_per_fixture.setdefault(fid, set()).add(pid)

    active_players = players[players["active"]] if not players.empty and "active" in players.columns else players

    fixture_blocks: list[str] = []

    for _, fix in upcoming.iterrows():
        fid = str(fix["fixture_id"])
        fix_lineups = lineups[lineups["fixture_id"] == fid]
        if fix_lineups.empty:
            continue

        dt = fix["date"].strftime("%Y-%m-%d") if pd.notna(fix["date"]) else "TBC"
        opp = shorten_team(opponent_name(fix, our_team))
        header = f"### {dt} vs {opp} (`{fid}`)\n"

        lines: list[str] = [header]
        unavailable_here = unavailable_per_fixture.get(fid, set())
        assigned_pids: set[str] = set(
            r for r in fix_lineups["player_id"].astype(str)
            if r and r != "nan"
        )

        for _, slot_row in fix_lineups.iterrows():
            slot = str(slot_row.get("position_slot", "")).strip()
            pid = str(slot_row.get("player_id", "")).strip()
            note = str(slot_row.get("notes", "")).strip() if pd.notna(slot_row.get("notes")) else ""

            if pid and pid != "nan":
                name = display_id(pid, id_map)
                warn = " ⚠️ UNAVAILABLE" if pid in unavailable_here else ""
                note_str = f" — {note}" if note else ""
                lines.append(f"- **{slot}**: {name}{warn}{note_str}")
            else:
                # Unfilled slot — suggest available players
                suggestions: list[str] = []
                if not active_players.empty:
                    for _, p in active_players.iterrows():
                        ppid = str(p["player_id"])
                        if ppid in unavailable_here:
                            continue
                        if ppid in assigned_pids:
                            continue
                        if slot in positions_for_player(p):
                            suggestions.append(display_id(ppid, id_map))
                note_str = f" ({note})" if note else ""
                if suggestions:
                    sug_str = ", ".join(suggestions)
                    lines.append(f"- **{slot}**: _unfilled_{note_str} — suggestions: {sug_str}")
                else:
                    lines.append(f"- **{slot}**: _unfilled_{note_str} — no eligible players found")

        fixture_blocks.append("\n".join(lines))

    if not fixture_blocks:
        return None

    return "## Lineup Status\n\n" + "\n\n".join(fixture_blocks)


def section_coach_focus(notes: pd.DataFrame, n: int = 3) -> str | None:
    if notes.empty or "focus_next_week" not in notes.columns:
        return None
    recent = notes.dropna(subset=["focus_next_week"]).tail(n)
    if recent.empty:
        return None
    lines = ["## Coach Focus Areas (Last 3 Entries)\n"]
    for _, row in recent.iterrows():
        fid = row.get("fixture_id", "?")
        focus = row["focus_next_week"]
        lines.append(f"**{fid}:** {focus}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build_report(team_hint: str | None, id_map: dict | None = None) -> str:
    if id_map is None:
        id_map = {}
    df = load_matches()
    notes = load_notes()
    tags = load_tags()
    players = load_players()
    attendance = load_attendance()
    lineups = load_lineups()

    our_team = detect_team(df, team_hint)
    played = played_matches(df, our_team)

    today_str = date.today().isoformat()
    header = f"# Match Insights Report\n\nGenerated: {today_str}  \nTeam: **{our_team}**\n"

    sections = [header]
    sections.append(section_season_summary(played, our_team))
    sections.append(section_form(played, our_team))
    sections.append(section_scoring_trend(played, our_team))
    sections.append(section_head_to_head(played, our_team))

    tag_section = section_tag_summary(tags)
    if tag_section:
        sections.append(tag_section)

    next_fix = section_next_fixture(df, our_team)
    if next_fix:
        sections.append(next_fix)

    lineup_section = section_lineup_status(df, our_team, players, attendance, lineups, id_map)
    if lineup_section:
        sections.append(lineup_section)

    focus_section = section_coach_focus(notes)
    if focus_section:
        sections.append(focus_section)

    return "\n\n---\n\n".join(sections) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a Markdown insights report.")
    parser.add_argument("--output", type=str, default="", help="Output path (default: reports/insights_YYYY-MM-DD.md).")
    parser.add_argument("--team", type=str, default="", help="Our team name (auto-detected if omitted).")
    parser.add_argument("--reveal", action="store_true",
        help="Replace player IDs with real names using secrets/player_id_map.csv")
    args = parser.parse_args()

    id_map = load_id_map() if args.reveal else {}
    report = build_report(args.team or None, id_map=id_map)

    today_str = date.today().isoformat()
    out_path = Path(args.output) if args.output else REPORTS_DIR / f"insights_{today_str}.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")
    print(f"Report written to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
