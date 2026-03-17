"""战斗属性重算服务。"""

from __future__ import annotations

from typing import Dict

from core.database.connection import get_user_by_id, update_user, get_item_by_db_id
from core.game.realms import calculate_user_stats


def recalculate_user_combat_stats(user_id: str, reset_current: bool = False) -> Dict:
    """Recalculate user stats from realm base + all equipped items.

    - Always updates: attack/defense/max_hp/max_mp
    - If reset_current=True: set hp/mp to max
    - Otherwise: clamp hp/mp to new max

    Returns the update dict that was applied.
    """
    user = get_user_by_id(user_id)
    if not user:
        return {}

    base = calculate_user_stats({"rank": user.get("rank", 1), "element": user.get("element")})
    atk = base["attack"]
    dfn = base["defense"]
    mhp = base["max_hp"]
    mmp = base["max_mp"]

    for slot in ("equipped_weapon", "equipped_armor", "equipped_accessory1", "equipped_accessory2"):
        db_id = user.get(slot)
        if not db_id:
            continue
        item = get_item_by_db_id(db_id)
        if not item:
            continue
        atk += item.get("attack_bonus", 0)
        dfn += item.get("defense_bonus", 0)
        mhp += item.get("hp_bonus", 0)
        mmp += item.get("mp_bonus", 0)

    updates = {"attack": atk, "defense": dfn, "max_hp": mhp, "max_mp": mmp}

    if reset_current:
        updates["hp"] = mhp
        updates["mp"] = mmp
    else:
        try:
            cur_hp = int(user.get("hp", mhp) or 0)
            cur_mp = int(user.get("mp", mmp) or 0)
        except Exception:
            cur_hp, cur_mp = mhp, mmp
        updates["hp"] = min(cur_hp, mhp)
        updates["mp"] = min(cur_mp, mmp)

    update_user(user_id, updates)
    return updates
