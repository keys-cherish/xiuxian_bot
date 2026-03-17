"""Quest service helpers (avoid importing core.server to prevent cycles)."""

from __future__ import annotations

from typing import Optional

from core.database.connection import fetch_one, upsert_quest
from core.game.quests import get_all_quest_defs
from core.utils.timeutil import today_local


def today_str() -> str:
    return today_local()


def ensure_daily_quests(user_id: str, day: Optional[str] = None) -> None:
    day = day or today_str()
    for qdef in get_all_quest_defs():
        upsert_quest(user_id, qdef["id"], day, 0, qdef["goal"])


def increment_quest(user_id: str, quest_id: str, amount: int = 1, day: Optional[str] = None) -> None:
    day = day or today_str()
    ensure_daily_quests(user_id, day)
    row = fetch_one(
        "SELECT id, progress, goal, claimed FROM user_quests WHERE user_id = ? AND quest_id = ? AND assigned_date = ?",
        (user_id, quest_id, day),
    )
    if not row:
        return
    if row.get("claimed"):
        return
    new_progress = int(row.get("progress", 0) or 0) + int(amount or 0)
    # cap to goal just in case
    goal = int(row.get("goal", 1) or 1)
    if new_progress > goal:
        new_progress = goal
    from core.database.connection import execute
    execute("UPDATE user_quests SET progress = ? WHERE id = ?", (new_progress, row["id"]))
