"""Account-related services (register, etc.).

Return (response_dict, http_status).
"""

from __future__ import annotations

import re
import psycopg2.errors
import time
from typing import Any, Dict, Tuple, Optional

from core.database.connection import (
    get_user_by_platform,
    get_user_by_username,
    db_transaction,
    VALID_PLATFORMS,
)
from core.utils.database import generate_universal_uid
from core.game.realms import ELEMENT_BONUSES


USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9\u4e00-\u9fff]{2,16}$")


def _validate_username(username: str) -> Optional[str]:
    username = (username or "").strip()
    if not username:
        return "游戏名不能为空"
    if not USERNAME_PATTERN.fullmatch(username):
        return "游戏名仅允许 2-16 位中文、字母或数字"
    return None


def register_account(*, platform: str, platform_id: str, username: str, element: Optional[str], lang: str) -> Tuple[Dict[str, Any], int]:
    if not platform or not platform_id:
        return {"success": False, "code": "MISSING_PARAMS", "message": "Missing parameters"}, 400
    platform = (platform or "").strip().lower()
    if platform not in VALID_PLATFORMS:
        return {"success": False, "code": "INVALID_PLATFORM", "message": "不支持的平台"}, 400

    existing = get_user_by_platform(platform, platform_id)
    if existing:
        return {
            "success": False,
            "code": "ALREADY_EXISTS",
            "message": "User already exists",
            "user_id": existing["user_id"],
            "lang": existing.get("lang", "CHS"),
        }, 400

    username = (username or "").strip()
    username_error = _validate_username(username)
    if username_error:
        return {"success": False, "code": "INVALID_USERNAME", "message": username_error}, 400

    try:
        uid = generate_universal_uid()
    except Exception:
        return {"success": False, "code": "UID_FAILED", "message": "UID generation failed"}, 500

    base_stats = {"hp": 100, "mp": 50, "attack": 10, "defense": 5, "crit_rate": 0.05}
    if element and element in ELEMENT_BONUSES:
        bonus = ELEMENT_BONUSES[element]
        base_stats["hp"] = int(base_stats["hp"] * (1 + bonus.get("hp", 0)))
        base_stats["mp"] = int(base_stats["mp"] * (1 + bonus.get("mp", 0)))
        base_stats["attack"] = int(base_stats["attack"] * (1 + bonus.get("attack", 0)))
        base_stats["defense"] = int(base_stats["defense"] * (1 + bonus.get("defense", 0)))
        base_stats["crit_rate"] = bonus.get("crit_rate", 0.05)

    try:
        with db_transaction() as cur:
            cur.execute(
                """
                INSERT INTO users (
                    user_id, in_game_username, lang, state, exp, rank, dy_times,
                    copper, gold, asc_reduction, sign, element,
                    hp, mp, max_hp, max_mp, attack, defense, crit_rate,
                    created_at, telegram_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    uid,
                    username,
                    lang,
                    0,
                    0,
                    1,
                    0,
                    0,
                    0,
                    0,
                    0,
                    element,
                    base_stats["hp"],
                    base_stats["mp"],
                    base_stats["hp"],
                    base_stats["mp"],
                    base_stats["attack"],
                    base_stats["defense"],
                    base_stats["crit_rate"],
                    int(time.time()),
                    platform_id if platform == "telegram" else "",
                ),
            )
    except psycopg2.errors.UniqueViolation as exc:
        err_text = str(exc).lower()
        existing = get_user_by_platform(platform, platform_id)
        if existing:
            return {
                "success": False,
                "code": "ALREADY_EXISTS",
                "message": "User already exists",
                "user_id": existing["user_id"],
                "lang": existing.get("lang", "CHS"),
            }, 400
        if "idx_users_telegram_id_unique" in err_text or "users.telegram_id" in err_text:
            return {"success": False, "code": "ALREADY_EXISTS", "message": "User already exists"}, 400
        if (
            "idx_users_username_unique" in err_text
            or "users.in_game_username" in err_text
            or "in_game_username" in err_text
        ):
            return {"success": False, "code": "USERNAME_TAKEN", "message": "该游戏名已被占用"}, 400
        if get_user_by_username(username):
            return {"success": False, "code": "USERNAME_TAKEN", "message": "该游戏名已被占用"}, 400
        return {"success": False, "code": "CONFLICT", "message": "账号注册冲突，请重试"}, 409

    return {
        "success": True,
        "user_id": uid,
        "username": username,
        "element": element,
    }, 200
