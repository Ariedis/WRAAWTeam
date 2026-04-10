"""Add a new player to secrets/player_id_map.csv and notes/players.csv.

Generates a random unique 6-digit player_id and appends one row to each file.

Usage:
    python scripts/add_player.py --name "Alice Brooks" --position GK
    python scripts/add_player.py --name "Beth Nguyen" --position CB --squad 5 --preferred "CB;LB"
"""
from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path

POSITIONS_PATH = Path("docs/positions.md")

import re

def load_approved_positions() -> set[str]:
    if not POSITIONS_PATH.exists():
        return set()
    return set(re.findall(r"\|\s+([A-Z]{2,5})\s+\|", POSITIONS_PATH.read_text(encoding="utf-8")))


def existing_ids(secrets_path: Path, players_path: Path) -> set[str]:
    ids: set[str] = set()
    for path in (secrets_path, players_path):
        if path.exists():
            with path.open(encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    pid = row.get("player_id", "").strip()
                    if pid:
                        ids.add(pid)
    return ids


def generate_id(taken: set[str]) -> str:
    while True:
        pid = str(random.randint(100000, 999999))
        if pid not in taken:
            return pid


def append_row(path: Path, row: dict) -> None:
    with path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        writer.writerow(row)


def main() -> int:
    parser = argparse.ArgumentParser(description="Add a new player and generate their ID.")
    parser.add_argument("--team-dir", type=str, required=True,
                        help="Path to the team directory (e.g. teams/WRR-AAW).")
    parser.add_argument("--name", required=True, help="Player's real name (written to secrets file only)")
    parser.add_argument("--position", required=True, help="Primary position code (e.g. GK, CB, ST)")
    parser.add_argument("--squad", type=int, default=None, help="Squad/shirt number (optional)")
    parser.add_argument("--preferred", default="", help="Semicolon-separated preferred positions (optional)")
    args = parser.parse_args()

    team_dir = Path(args.team_dir)
    secrets_path = team_dir / "secrets" / "player_id_map.csv"
    players_path = team_dir / "notes" / "players.csv"

    approved = load_approved_positions()
    if approved:
        if args.position not in approved:
            print(f"ERROR: '{args.position}' is not an approved position code.")
            print(f"Approved codes: {', '.join(sorted(approved))}")
            return 1
        for code in [p.strip() for p in args.preferred.split(";") if p.strip()]:
            if code not in approved:
                print(f"ERROR: preferred position '{code}' is not an approved position code.")
                print(f"Approved codes: {', '.join(sorted(approved))}")
                return 1

    if not secrets_path.parent.exists():
        secrets_path.parent.mkdir(parents=True)

    taken = existing_ids(secrets_path, players_path)
    player_id = generate_id(taken)

    append_row(secrets_path, {"player_id": player_id, "player_name": args.name})
    append_row(players_path, {
        "player_id": player_id,
        "squad_number": args.squad if args.squad is not None else "",
        "primary_position": args.position,
        "preferred_positions": args.preferred,
        "active": "TRUE",
    })

    print(f"Added player '{args.name}' with player_id {player_id}")
    print(f"  {secrets_path}  — name recorded")
    print(f"  {players_path}  — squad row added (share this ID with the coach)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
