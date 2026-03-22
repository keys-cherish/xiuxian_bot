"""
宗门古塔（试炼塔）系统 - Tower Service

每日可挑战 1 次，从当前最高通过层+1 开始，每层生成守卫自动战斗，
直到失败为止。可消耗修为重置进度。
"""

from __future__ import annotations

import logging
import random
from typing import Any, Dict, List, Tuple

from core.database.connection import (
    db_transaction,
    fetch_one,
    get_user_by_id,
    get_user_skills,
)
from core.game.combat import Combat, create_combatant_from_user
from core.game.realms import get_realm_by_id, format_realm_display, REALMS
from core.utils.timeutil import local_day_key

logger = logging.getLogger("core.tower")

# ── 配置常量 ──────────────────────────────────────────────────────
MAX_FLOOR = len(REALMS)          # 最高层数 = 境界总数
GUARDIAN_STAT_MULTIPLIER = 1.2   # 守卫属性倍率（略强于同境界玩家）
REWARD_COPPER_PER_FLOOR = 5      # 每层通过奖励灵石系数
REWARD_EXP_PER_FLOOR = 3         # 每层通过奖励修为系数
LOSS_EXP_PER_FLOOR = 2           # 失败层损失修为系数
RESET_COST_PER_FLOOR = 100       # 重置消耗修为系数（当前层数 * 此值）
MAX_RESETS_PER_DAY = 3           # 每日重置次数上限


def _create_tower_guardian(floor: int) -> Dict[str, Any]:
    """生成第 N 层守卫。

    层数直接对应 realm_id，用该境界的基础属性 * 1.2 生成守卫。
    返回格式兼容 Combat 系统的 combatant dict。
    """
    realm = get_realm_by_id(floor)
    if realm is None:
        # 超出已定义境界时，使用最高境界并按比例增强
        realm = REALMS[-1]
        overflow = floor - realm["id"]
        scale = GUARDIAN_STAT_MULTIPLIER * (1.0 + overflow * 0.15)
    else:
        scale = GUARDIAN_STAT_MULTIPLIER

    base_hp = int(realm["hp"] * scale)
    base_mp = int(realm["mp"] * scale)
    base_atk = int(realm["attack"] * scale)
    base_def = int(realm["defense"] * scale)

    # 随机选择元素增加趣味性
    elements = ["金", "木", "水", "火", "土"]
    element = random.choice(elements)

    realm_display = format_realm_display(floor) if get_realm_by_id(floor) else f"第{floor}层"

    return {
        "name": f"{realm_display}守卫",
        "hp": base_hp,
        "max_hp": base_hp,
        "mp": base_mp,
        "max_mp": base_mp,
        "attack": base_atk,
        "defense": base_def,
        "crit_rate": 0.03 + floor * 0.001,  # 随层数微增暴击
        "element": element,
    }


def _get_today_key() -> int:
    """获取今日日期序号（北京时间）。"""
    return local_day_key()


def get_tower_status(user_id: str) -> dict:
    """获取用户古塔状态。"""
    user = get_user_by_id(user_id)
    if not user:
        return {"success": False, "message": "用户不存在"}

    floor = int(user.get("tower_floor", 0) or 0)
    last_day = int(user.get("tower_last_attempt_day", 0) or 0)
    resets_today = int(user.get("tower_resets_today", 0) or 0)
    today = _get_today_key()

    # 跨日重置挑战状态
    can_challenge = (last_day != today)

    # 下一层信息
    next_floor = floor + 1
    next_realm = get_realm_by_id(next_floor)
    next_display = format_realm_display(next_floor) if next_realm else f"第{next_floor}层"

    # 重置消耗
    reset_cost = floor * RESET_COST_PER_FLOOR if floor > 0 else 0

    return {
        "success": True,
        "tower_floor": floor,
        "can_challenge": can_challenge,
        "challenged_today": (last_day == today),
        "next_floor": next_floor,
        "next_floor_display": next_display,
        "resets_today": resets_today if last_day == today else 0,
        "max_resets_per_day": MAX_RESETS_PER_DAY,
        "reset_cost_exp": reset_cost,
        "max_floor": MAX_FLOOR,
    }


def attempt_tower(user_id: str) -> Tuple[dict, int]:
    """挑战古塔。

    从当前最高通过层+1 开始，每层自动战斗，直到失败为止。
    返回 (response_dict, http_status)。
    """
    user = get_user_by_id(user_id)
    if not user:
        return {"success": False, "message": "用户不存在"}, 404

    floor = int(user.get("tower_floor", 0) or 0)
    last_day = int(user.get("tower_last_attempt_day", 0) or 0)
    today = _get_today_key()

    if last_day == today:
        return {"success": False, "message": "今日已挑战过古塔，明日再来。"}, 400

    # 获取用户技能用于构建战斗体
    learned_skills = get_user_skills(user_id)

    # 闯塔循环
    battle_log: List[Dict[str, Any]] = []
    floors_cleared = 0
    total_copper = 0
    total_exp = 0
    current_floor = floor + 1
    failed_floor = 0

    # 构建用户战斗体（HP/MP 保持满血进入）
    user_combatant = create_combatant_from_user(user, learned_skills)

    while current_floor <= MAX_FLOOR:
        guardian = _create_tower_guardian(current_floor)
        realm_display = format_realm_display(current_floor) if get_realm_by_id(current_floor) else f"第{current_floor}层"

        # 战斗
        combat = Combat(dict(user_combatant), dict(guardian))
        result = combat.fight()

        if result["winner"] == "attacker":
            # 胜利：记录层数，计算奖励
            copper_reward = current_floor * REWARD_COPPER_PER_FLOOR
            exp_reward = current_floor * REWARD_EXP_PER_FLOOR
            total_copper += copper_reward
            total_exp += exp_reward
            floors_cleared += 1

            battle_log.append({
                "floor": current_floor,
                "realm_display": realm_display,
                "victory": True,
                "message": f"险胜：经过一番苦战，你成功击碎了守卫核心！",
                "rounds": result["rounds"],
            })

            # 保持剩余 HP/MP 到下一层
            user_combatant["hp"] = max(1, result.get("attacker_remaining_hp", 1))
            user_combatant["mp"] = max(0, result.get("attacker_remaining_mp", 0))

            current_floor += 1
        else:
            # 失败
            failed_floor = current_floor
            exp_loss = current_floor * LOSS_EXP_PER_FLOOR

            battle_log.append({
                "floor": current_floor,
                "realm_display": realm_display,
                "victory": False,
                "message": f"败北：守卫实力深不可测，你力战不敌，被打出塔外！",
                "rounds": result["rounds"],
            })

            # 扣修为不低于 0
            total_exp -= exp_loss
            break

    # 最终通过层 = 原来的层数 + 本次通过层数
    new_floor = floor + floors_cleared

    # 写入数据库（事务）
    with db_transaction() as cur:
        # 更新古塔状态
        cur.execute(
            """UPDATE users
               SET tower_floor = %s,
                   tower_last_attempt_day = %s,
                   copper = copper + %s,
                   exp = GREATEST(0, exp + %s)
               WHERE user_id = %s""",
            (new_floor, today, max(0, total_copper), total_exp, user_id),
        )

    # 构建战报
    summary_lines = []
    for entry in battle_log:
        tag = "险胜" if entry["victory"] else "败北"
        summary_lines.append(
            f"- 第 {entry['floor']} 层 ({entry['realm_display']}): "
            f"{entry['message']}"
        )

    # 总收获描述
    reward_parts = [f"本次共闯过 {floors_cleared} 层。"]
    if total_exp >= 0:
        reward_parts.append(f"获得了 {total_exp} 点修为。")
    else:
        reward_parts.append(f"修为 损失了 {abs(total_exp)} 点。")
    if total_copper > 0:
        reward_parts.append(f"获得了【灵石】x{total_copper}")

    return {
        "success": True,
        "tower_floor": new_floor,
        "floors_cleared": floors_cleared,
        "failed_floor": failed_floor,
        "battle_log": battle_log,
        "summary": "\n".join(summary_lines),
        "rewards": {
            "copper": max(0, total_copper),
            "exp": total_exp,
        },
        "reward_summary": " ".join(reward_parts),
    }, 200


def reset_tower(user_id: str) -> Tuple[dict, int]:
    """重置古塔进度。

    消耗: 当前层数 * 100 修为。
    效果: 重置最高通过层为 0，可重新挑战。
    """
    user = get_user_by_id(user_id)
    if not user:
        return {"success": False, "message": "用户不存在"}, 404

    floor = int(user.get("tower_floor", 0) or 0)
    if floor == 0:
        return {"success": False, "message": "你还未通过任何层，无需重置。"}, 400

    today = _get_today_key()
    last_day = int(user.get("tower_last_attempt_day", 0) or 0)

    # 跨日重置计数
    resets_today = int(user.get("tower_resets_today", 0) or 0) if last_day == today else 0

    if resets_today >= MAX_RESETS_PER_DAY:
        return {"success": False, "message": f"今日已重置 {MAX_RESETS_PER_DAY} 次，无法再重置。"}, 400

    cost = floor * RESET_COST_PER_FLOOR
    current_exp = int(user.get("exp", 0) or 0)

    if current_exp < cost:
        return {
            "success": False,
            "message": f"修为不足！重置需要消耗 {cost} 修为（当前层数 {floor} x {RESET_COST_PER_FLOOR}），你当前只有 {current_exp} 修为。",
        }, 400

    with db_transaction() as cur:
        cur.execute(
            """UPDATE users
               SET tower_floor = 0,
                   tower_last_attempt_day = 0,
                   tower_resets_today = %s,
                   exp = exp - %s
               WHERE user_id = %s""",
            (resets_today + 1, cost, user_id),
        )

    return {
        "success": True,
        "message": f"古塔进度已重置！消耗了 {cost} 修为。你可以重新挑战。",
        "cost_exp": cost,
        "resets_today": resets_today + 1,
    }, 200
