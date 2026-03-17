"""Breakthrough pity / compensation service.

Mechanics:
- On failure: increase pity counter.
- Each pity point increases next success rate by +2% (cap +20%).
- Hard pity: after N consecutive failures, guaranteed success.
- When breakthrough succeeds: pity resets to 0.

DB: users.breakthrough_pity INTEGER
"""

from __future__ import annotations

from typing import Dict, Any


PITY_BONUS_PER_POINT = 0.02
PITY_BONUS_MAX = 0.20

# 硬保底次数表 - 按境界ID区间划分
# 连续失败达到该次数后，下一次必定成功
HARD_PITY_TABLE = {
    (1, 5):   5,     # 练气期: 5次必成
    (6, 9):   8,     # 筑基期: 8次必成
    (10, 13): 12,    # 金丹期: 12次必成
    (14, 17): 18,    # 元婴期: 18次必成
    (18, 21): 25,    # 化神期: 25次必成
    (22, 25): 35,    # 炼虚期: 35次必成
    (26, 29): 50,    # 合体期: 50次必成
    (30, 31): 80,    # 大乘/渡劫: 80次必成
}

DEFAULT_HARD_PITY = 100


def get_hard_pity_threshold(realm_id: int) -> int:
    """获取指定境界的硬保底次数"""
    realm_id = int(realm_id or 1)
    for (low, high), threshold in HARD_PITY_TABLE.items():
        if low <= realm_id <= high:
            return threshold
    return DEFAULT_HARD_PITY


def bonus(pity: int) -> float:
    """计算保底加成概率"""
    pity = int(pity or 0)
    if pity <= 0:
        return 0.0
    b = pity * PITY_BONUS_PER_POINT
    if b > PITY_BONUS_MAX:
        b = PITY_BONUS_MAX
    return b


def is_hard_pity(pity: int, realm_id: int) -> bool:
    """判断是否触发硬保底（下一次必定成功）"""
    pity = int(pity or 0)
    threshold = get_hard_pity_threshold(realm_id)
    return pity >= threshold


def apply_on_failure(user: Dict[str, Any]) -> Dict[str, Any]:
    """失败时增加保底计数"""
    pity = int(user.get("breakthrough_pity", 0) or 0)
    pity += 1
    return {"breakthrough_pity": pity}


def apply_on_success(_: Dict[str, Any]) -> Dict[str, Any]:
    """成功时重置保底计数"""
    return {"breakthrough_pity": 0}
