"""Codex / collection tracking service.

Tracks first-seen + counts for monsters and items.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List

from core.database.connection import execute, fetch_one, fetch_all


def ensure_monster(user_id: str, monster_id: str) -> None:
    now = int(time.time())
    row = fetch_one(
        "SELECT id, kills FROM codex_monsters WHERE user_id = ? AND monster_id = ?",
        (user_id, monster_id),
    )
    if row:
        execute(
            "UPDATE codex_monsters SET kills = kills + 1, last_seen_at = ? WHERE id = ?",
            (now, row["id"]),
        )
        return
    execute(
        "INSERT INTO codex_monsters(user_id, monster_id, first_seen_at, last_seen_at, kills) VALUES (?, ?, ?, ?, 1)",
        (user_id, monster_id, now, now),
    )


def ensure_item(user_id: str, item_id: str, qty: int = 1) -> None:
    now = int(time.time())
    row = fetch_one(
        "SELECT id, total_obtained FROM codex_items WHERE user_id = ? AND item_id = ?",
        (user_id, item_id),
    )
    qty = int(qty or 1)
    if row:
        execute(
            "UPDATE codex_items SET total_obtained = total_obtained + ?, last_seen_at = ? WHERE id = ?",
            (qty, now, row["id"]),
        )
        return
    execute(
        "INSERT INTO codex_items(user_id, item_id, first_seen_at, last_seen_at, total_obtained) VALUES (?, ?, ?, ?, ?)",
        (user_id, item_id, now, now, qty),
    )


def list_monsters(user_id: str) -> List[Dict[str, Any]]:
    return fetch_all(
        "SELECT monster_id, kills, first_seen_at, last_seen_at FROM codex_monsters WHERE user_id = ? ORDER BY kills DESC, last_seen_at DESC",
        (user_id,),
    )


def list_items(user_id: str) -> List[Dict[str, Any]]:
    return fetch_all(
        "SELECT item_id, total_obtained, first_seen_at, last_seen_at FROM codex_items WHERE user_id = ? ORDER BY total_obtained DESC, last_seen_at DESC",
        (user_id,),
    )
