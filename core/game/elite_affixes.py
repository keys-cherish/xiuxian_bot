from __future__ import annotations

import random
from typing import Dict, List, Tuple

AFFIX_DEFS: List[Dict[str, object]] = [
    {
        "key": "bloodthirst",
        "name": "嗜血",
        "lifesteal": 0.12,
    },
    {
        "key": "thick_armor",
        "name": "厚甲",
        "damage_taken_mul": 0.85,
    },
    {
        "key": "swift",
        "name": "迅捷",
        "crit_rate": 0.08,
        "damage_mul": 1.12,
    },
    {
        "key": "poison",
        "name": "剧毒",
        "poison_pct": 0.15,
    },
    {
        "key": "thorns",
        "name": "反震",
        "thorns_pct": 0.12,
    },
    {
        "key": "enrage",
        "name": "残血狂暴",
        "enrage_threshold": 0.35,
        "enrage_damage_mul": 1.25,
    },
    {
        "key": "first_hit_shield",
        "name": "首击护盾",
        "first_hit_shield_pct": 0.20,
    },
    {
        "key": "counter_boost",
        "name": "反击强化",
        "counter_bonus_pct": 0.18,
    },
]

AFFIX_MAP = {a["key"]: a for a in AFFIX_DEFS}

ELITE_CHANCE = {
    "hunt": 0.15,
    "secret": 0.22,
}


def _affix_count_for_rank(user_rank: int) -> int:
    count = 1
    if int(user_rank or 1) >= 12 and random.random() < 0.35:
        count = 2
    if int(user_rank or 1) >= 20 and random.random() < 0.15:
        count = 3
    return min(count, len(AFFIX_DEFS))


def roll_elite_affixes(*, user_rank: int, source_kind: str = "hunt") -> Tuple[List[str], List[str]]:
    chance = float(ELITE_CHANCE.get(source_kind, 0.15) or 0.15)
    if random.random() >= chance:
        return [], []
    count = _affix_count_for_rank(user_rank)
    pool = list(AFFIX_DEFS)
    random.shuffle(pool)
    picked = pool[:count]
    keys = [p["key"] for p in picked]
    names = [p["name"] for p in picked]
    return keys, names


def apply_elite_affixes(combatant: Dict[str, object], affix_keys: List[str]) -> None:
    if not affix_keys:
        return
    combatant["elite"] = True
    combatant["elite_affixes"] = list(affix_keys)
    combatant["elite_affix_names"] = [AFFIX_MAP.get(k, {}).get("name", k) for k in affix_keys]

    combatant.setdefault("lifesteal", 0.0)
    combatant.setdefault("damage_mul", 1.0)
    combatant.setdefault("damage_taken_mul", 1.0)
    combatant.setdefault("crit_rate", 0.03)
    combatant.setdefault("poison_pct", 0.0)
    combatant.setdefault("thorns_pct", 0.0)
    combatant.setdefault("enrage_threshold", 0.0)
    combatant.setdefault("enrage_damage_mul", 1.0)
    combatant.setdefault("first_hit_shield_pct", 0.0)
    combatant.setdefault("counter_bonus_pct", 0.0)

    for key in affix_keys:
        aff = AFFIX_MAP.get(key)
        if not aff:
            continue
        if aff.get("lifesteal"):
            combatant["lifesteal"] = float(combatant.get("lifesteal", 0.0) or 0.0) + float(aff["lifesteal"])
        if aff.get("damage_taken_mul"):
            combatant["damage_taken_mul"] = float(combatant.get("damage_taken_mul", 1.0) or 1.0) * float(aff["damage_taken_mul"])
        if aff.get("damage_mul"):
            combatant["damage_mul"] = float(combatant.get("damage_mul", 1.0) or 1.0) * float(aff["damage_mul"])
        if aff.get("crit_rate"):
            combatant["crit_rate"] = float(combatant.get("crit_rate", 0.03) or 0.03) + float(aff["crit_rate"])
        if aff.get("poison_pct"):
            combatant["poison_pct"] = float(combatant.get("poison_pct", 0.0) or 0.0) + float(aff["poison_pct"])
        if aff.get("thorns_pct"):
            combatant["thorns_pct"] = float(combatant.get("thorns_pct", 0.0) or 0.0) + float(aff["thorns_pct"])
        if aff.get("enrage_threshold"):
            combatant["enrage_threshold"] = float(aff.get("enrage_threshold"))
        if aff.get("enrage_damage_mul"):
            combatant["enrage_damage_mul"] = float(combatant.get("enrage_damage_mul", 1.0) or 1.0) * float(aff.get("enrage_damage_mul"))
        if aff.get("first_hit_shield_pct"):
            combatant["first_hit_shield_pct"] = float(combatant.get("first_hit_shield_pct", 0.0) or 0.0) + float(aff.get("first_hit_shield_pct"))
        if aff.get("counter_bonus_pct"):
            combatant["counter_bonus_pct"] = float(combatant.get("counter_bonus_pct", 0.0) or 0.0) + float(aff.get("counter_bonus_pct"))

    combatant["lifesteal"] = min(0.5, float(combatant.get("lifesteal", 0.0) or 0.0))
    combatant["poison_pct"] = min(0.5, float(combatant.get("poison_pct", 0.0) or 0.0))
    combatant["thorns_pct"] = min(0.5, float(combatant.get("thorns_pct", 0.0) or 0.0))
    combatant["crit_rate"] = min(0.5, float(combatant.get("crit_rate", 0.03) or 0.03))
    combatant["first_hit_shield_pct"] = min(0.45, float(combatant.get("first_hit_shield_pct", 0.0) or 0.0))
    combatant["counter_bonus_pct"] = min(0.5, float(combatant.get("counter_bonus_pct", 0.0) or 0.0))
