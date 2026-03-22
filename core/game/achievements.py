"""Achievement definitions -- grouped by cultivation stage."""

from __future__ import annotations

from typing import Dict, Any, List, Optional


ACHIEVEMENTS = [
    # === 练气期 (rank 1-5) ===
    {"id": "lianqi_hunt_10", "name": "初出茅庐", "desc": "累计狩猎10次", "type": "hunt_count", "goal": 10,
     "stage": "lianqi", "stage_name": "练气期", "min_rank": 1, "max_rank": 5,
     "rewards": {"copper": 200, "exp": 100}},
    {"id": "lianqi_cultivate_5", "name": "初窥门径", "desc": "累计修炼5次", "type": "cultivate_count", "goal": 5,
     "stage": "lianqi", "stage_name": "练气期", "min_rank": 1, "max_rank": 5,
     "rewards": {"copper": 150, "exp": 80}},
    {"id": "lianqi_rank_5", "name": "练气圆满", "desc": "突破至练气圆满", "type": "rank_reach", "goal": 5,
     "stage": "lianqi", "stage_name": "练气期", "min_rank": 1, "max_rank": 5,
     "rewards": {"copper": 500, "exp": 300}},
    {"id": "lianqi_skill_1", "name": "习得一技", "desc": "学习1个技能", "type": "skill_count", "goal": 1,
     "stage": "lianqi", "stage_name": "练气期", "min_rank": 1, "max_rank": 5,
     "rewards": {"copper": 200, "exp": 100}},

    # === 筑基期 (rank 6-9) ===
    {"id": "zhuji_hunt_50", "name": "百战猎手", "desc": "累计狩猎50次", "type": "hunt_count", "goal": 50,
     "stage": "zhuji", "stage_name": "筑基期", "min_rank": 6, "max_rank": 9,
     "rewards": {"copper": 500, "exp": 300}},
    {"id": "zhuji_rank_9", "name": "筑基圆满", "desc": "突破至筑基圆满", "type": "rank_reach", "goal": 9,
     "stage": "zhuji", "stage_name": "筑基期", "min_rank": 6, "max_rank": 9,
     "rewards": {"copper": 800, "exp": 500}},
    {"id": "zhuji_secret_5", "name": "秘境探索者", "desc": "完成5次秘境探索", "type": "secret_realm_count", "goal": 5,
     "stage": "zhuji", "stage_name": "筑基期", "min_rank": 6, "max_rank": 9,
     "rewards": {"copper": 600, "exp": 400}},
    {"id": "zhuji_skill_3", "name": "三艺精通", "desc": "学习3个技能", "type": "skill_count", "goal": 3,
     "stage": "zhuji", "stage_name": "筑基期", "min_rank": 6, "max_rank": 9,
     "rewards": {"copper": 500, "exp": 300}},
    {"id": "zhuji_pvp_5", "name": "试剑天下", "desc": "PVP胜利5次", "type": "pvp_wins", "goal": 5,
     "stage": "zhuji", "stage_name": "筑基期", "min_rank": 6, "max_rank": 9,
     "rewards": {"copper": 600, "exp": 400}},

    # === 金丹期 (rank 10-13) ===
    {"id": "jindan_hunt_100", "name": "猎妖人", "desc": "累计狩猎100次", "type": "hunt_count", "goal": 100,
     "stage": "jindan", "stage_name": "金丹期", "min_rank": 10, "max_rank": 13,
     "rewards": {"copper": 900, "exp": 600, "gold": 1}},
    {"id": "jindan_rank_13", "name": "金丹大圆满", "desc": "突破至金丹圆满", "type": "rank_reach", "goal": 13,
     "stage": "jindan", "stage_name": "金丹期", "min_rank": 10, "max_rank": 13,
     "rewards": {"copper": 1200, "exp": 800, "gold": 2}},
    {"id": "jindan_breakthrough_10", "name": "破境之路", "desc": "突破成功10次", "type": "breakthrough_success", "goal": 10,
     "stage": "jindan", "stage_name": "金丹期", "min_rank": 10, "max_rank": 13,
     "rewards": {"copper": 1000, "exp": 700, "gold": 1}},
    {"id": "jindan_skill_5", "name": "五艺俱全", "desc": "学习5个技能", "type": "skill_count", "goal": 5,
     "stage": "jindan", "stage_name": "金丹期", "min_rank": 10, "max_rank": 13,
     "rewards": {"copper": 800, "exp": 500, "gold": 1}},
    {"id": "jindan_forge_3", "name": "初涉锻造", "desc": "锻造3件装备", "type": "forge_count", "goal": 3,
     "stage": "jindan", "stage_name": "金丹期", "min_rank": 10, "max_rank": 13,
     "rewards": {"copper": 700, "exp": 400}},

    # === 元婴期 (rank 14-17) ===
    {"id": "yuanying_rank_17", "name": "元婴大圆满", "desc": "突破至元婴圆满", "type": "rank_reach", "goal": 17,
     "stage": "yuanying", "stage_name": "元婴期", "min_rank": 14, "max_rank": 17,
     "rewards": {"copper": 1800, "exp": 1200, "gold": 3}},
    {"id": "yuanying_hunt_200", "name": "百战不殆", "desc": "累计狩猎200次", "type": "hunt_count", "goal": 200,
     "stage": "yuanying", "stage_name": "元婴期", "min_rank": 14, "max_rank": 17,
     "rewards": {"copper": 1500, "exp": 1000, "gold": 2}},
    {"id": "yuanying_pvp_20", "name": "修罗战场", "desc": "PVP胜利20次", "type": "pvp_wins", "goal": 20,
     "stage": "yuanying", "stage_name": "元婴期", "min_rank": 14, "max_rank": 17,
     "rewards": {"copper": 1200, "exp": 900, "gold": 2}},
    {"id": "yuanying_quest_50", "name": "勤修不辍", "desc": "完成50次每日任务", "type": "quest_complete", "goal": 50,
     "stage": "yuanying", "stage_name": "元婴期", "min_rank": 14, "max_rank": 17,
     "rewards": {"copper": 1000, "exp": 800, "gold": 1}},

    # === 化神期+ (rank 18+) ===
    {"id": "huashen_rank_21", "name": "化神大圆满", "desc": "突破至化神圆满", "type": "rank_reach", "goal": 21,
     "stage": "huashen", "stage_name": "化神期", "min_rank": 18, "max_rank": 999,
     "rewards": {"copper": 2500, "exp": 1800, "gold": 5}},
    {"id": "huashen_hunt_500", "name": "万妖克星", "desc": "累计狩猎500次", "type": "hunt_count", "goal": 500,
     "stage": "huashen", "stage_name": "化神期", "min_rank": 18, "max_rank": 999,
     "rewards": {"copper": 2000, "exp": 1500, "gold": 3}},
    {"id": "huashen_skill_max", "name": "武学宗师", "desc": "任意技能提升到5级", "type": "skill_level", "goal": 5,
     "stage": "huashen", "stage_name": "化神期", "min_rank": 18, "max_rank": 999,
     "rewards": {"copper": 1500, "exp": 1200, "gold": 2}},
]

# Pre-built index for fast ID lookup
_ACH_BY_ID: Dict[str, Dict[str, Any]] = {a["id"]: a for a in ACHIEVEMENTS}

# Stage ordering (for display)
STAGE_ORDER = ["lianqi", "zhuji", "jindan", "yuanying", "huashen"]


def list_achievements() -> List[Dict[str, Any]]:
    """Return all achievements (flat list, backward compatible)."""
    return [a.copy() for a in ACHIEVEMENTS]


def get_achievement(ach_id: str) -> Optional[Dict[str, Any]]:
    """Return a single achievement by id, or None."""
    a = _ACH_BY_ID.get(ach_id)
    return a.copy() if a else None


def list_achievements_by_stage(stage: str) -> List[Dict[str, Any]]:
    """Return achievements filtered by stage key (e.g. 'lianqi', 'zhuji')."""
    return [a.copy() for a in ACHIEVEMENTS if a.get("stage") == stage]


def get_current_stage_achievements(rank: int) -> List[Dict[str, Any]]:
    """Return achievements whose stage covers the given rank."""
    rank = int(rank or 1)
    return [
        a.copy() for a in ACHIEVEMENTS
        if int(a.get("min_rank", 0)) <= rank <= int(a.get("max_rank", 999))
    ]
