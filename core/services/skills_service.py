from __future__ import annotations

import time
from typing import Any, Dict, Optional, Tuple

from core.database.connection import fetch_one, execute, db_transaction, get_user_by_id

SKILL_MAX_LEVEL = 5

BOOK_EXP = {
    "skill_book_basic": 10,
    "skill_book_advanced": 25,
}


def mastery_required(level: int) -> int:
    lvl = max(1, int(level or 1))
    return 10 + (lvl - 1) * 10


def gain_skill_mastery(
    user_id: str,
    skill_id: str,
    amount: int = 1,
    *,
    now: Optional[int] = None,
    cur=None,
) -> Optional[Dict[str, Any]]:
    if amount <= 0:
        return None
    now_ts = int(time.time()) if now is None else int(now)
    if cur is None:
        row = fetch_one(
            "SELECT id, skill_level, mastery_exp FROM user_skills WHERE user_id = ? AND skill_id = ?",
            (user_id, skill_id),
        )
        if not row:
            return None
        level = int(row.get("skill_level", 1) or 1)
        exp = int(row.get("mastery_exp", 0) or 0) + int(amount)
        old_level = level
        while level < SKILL_MAX_LEVEL:
            need = mastery_required(level)
            if exp < need:
                break
            exp -= need
            level += 1
        execute(
            "UPDATE user_skills SET skill_level = ?, mastery_exp = ?, last_used_at = ? WHERE id = ?",
            (level, exp, now_ts, row["id"]),
        )
        return {"skill_level": level, "mastery_exp": exp, "leveled_up": level > old_level}

    row = cur.execute(
        "SELECT id, skill_level, mastery_exp FROM user_skills WHERE user_id = ? AND skill_id = ?",
        (user_id, skill_id),
    ).fetchone()
    if not row:
        return None
    level = int(row["skill_level"] or 1)
    exp = int(row["mastery_exp"] or 0) + int(amount)
    old_level = level
    while level < SKILL_MAX_LEVEL:
        need = mastery_required(level)
        if exp < need:
            break
        exp -= need
        level += 1
    cur.execute(
        "UPDATE user_skills SET skill_level = ?, mastery_exp = ?, last_used_at = ? WHERE id = ?",
        (level, exp, now_ts, row["id"]),
    )
    return {"skill_level": level, "mastery_exp": exp, "leveled_up": level > old_level}


def use_skill_book(
    *,
    user_id: str,
    skill_id: str,
    book_id: str,
) -> Tuple[Dict[str, Any], int]:
    user = get_user_by_id(user_id)
    if not user:
        return {"success": False, "code": "USER_NOT_FOUND", "message": "User not found"}, 404
    if not skill_id or not book_id:
        return {"success": False, "code": "MISSING_PARAMS", "message": "Missing parameters"}, 400
    exp_gain = BOOK_EXP.get(book_id)
    if not exp_gain:
        return {"success": False, "code": "INVALID", "message": "技能书不存在"}, 400
    with db_transaction() as cur:
        row = cur.execute(
            "SELECT id, quantity FROM items WHERE user_id = ? AND item_id = ? AND item_type = 'skill_book' ORDER BY id ASC LIMIT 1",
            (user_id, book_id),
        ).fetchone()
        if not row or int(row["quantity"] or 0) <= 0:
            return {"success": False, "code": "NOT_FOUND", "message": "技能书数量不足"}, 400
        if int(row["quantity"] or 0) == 1:
            cur.execute("DELETE FROM items WHERE id = ? AND user_id = ?", (row["id"], user_id))
        else:
            cur.execute(
                "UPDATE items SET quantity = quantity - 1 WHERE id = ? AND user_id = ? AND quantity > 0",
                (row["id"], user_id),
            )
            if cur.rowcount == 0:
                return {"success": False, "code": "NOT_FOUND", "message": "技能书数量不足"}, 400
        mastery = gain_skill_mastery(user_id, skill_id, exp_gain, cur=cur)
        if not mastery:
            return {"success": False, "code": "INVALID", "message": "尚未学会该技能"}, 400

    return {
        "success": True,
        "message": "使用技能书成功",
        "skill_id": skill_id,
        "book_id": book_id,
        "mastery_gain": exp_gain,
        "skill_level": mastery.get("skill_level"),
        "mastery_exp": mastery.get("mastery_exp"),
        "leveled_up": mastery.get("leveled_up"),
    }, 200
