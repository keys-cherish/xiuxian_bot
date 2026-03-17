"""Targeted drop pity (soft guarantee) helpers."""

from __future__ import annotations

import time
from typing import Any, Dict, Tuple

from core.config import config
from core.database.connection import db_transaction, fetch_one
from core.game.items import roll_targeted_equipment_drop


def _pity_key(source_kind: str, source_id: str) -> str:
    return f"{str(source_kind or '').strip()}:{str(source_id or '').strip()}"


def _pity_cfg() -> Dict[str, Any]:
    cfg = config.get_nested("balance", "drop_pity", default={}) or {}
    return {
        "enabled": bool(cfg.get("enabled", True)),
        "step": max(0.0, float(cfg.get("step", 0.015) or 0.015)),
        "cap": max(0.0, float(cfg.get("cap", 0.30) or 0.30)),
        "streak_cap": max(1, int(cfg.get("streak_cap", 50) or 50)),
    }


def roll_targeted_drop_with_pity(
    *,
    user_id: str,
    source_kind: str,
    source_id: str,
    user_rank: int,
    boosted: bool = False,
) -> Tuple[Dict[str, Any] | None, Dict[str, Any]]:
    cfg = _pity_cfg()
    pity_key = _pity_key(source_kind, source_id)
    streak = 0
    if cfg["enabled"]:
        row = fetch_one(
            "SELECT streak FROM drop_pity WHERE user_id = ? AND pity_key = ?",
            (user_id, pity_key),
        )
        streak = max(0, int((row or {}).get("streak", 0) or 0))
    pity_state = {"streak": streak, "step": cfg["step"], "cap": cfg["cap"]} if cfg["enabled"] else None
    drop, drop_meta = roll_targeted_equipment_drop(
        source_id,
        source_kind=source_kind,
        user_rank=int(user_rank or 1),
        boosted=bool(boosted),
        pity_state=pity_state,
        return_meta=True,
    )

    if cfg["enabled"]:
        new_streak = 0 if drop else min(int(cfg["streak_cap"]), streak + 1)
        now = int(time.time())
        with db_transaction() as cur:
            cur.execute(
                """
                INSERT INTO drop_pity(user_id, pity_key, streak, updated_at)
                VALUES(?,?,?,?)
                ON CONFLICT(user_id, pity_key)
                DO UPDATE SET streak = excluded.streak, updated_at = excluded.updated_at
                """,
                (user_id, pity_key, int(new_streak), now),
            )
    else:
        new_streak = 0
    meta = {
        "pity_key": pity_key,
        "enabled": bool(cfg["enabled"]),
        "previous_streak": int(streak),
        "next_streak": int(new_streak),
        **(drop_meta or {}),
    }
    return drop, meta
