"""Alchemy (pill crafting) definitions."""

from __future__ import annotations

from typing import Dict, Any, List, Optional


RECIPES = [
    {
        "id": "recipe_small_exp",
        "name": "小修为丹",
        "category": "stage_goal",
        "product_item_id": "small_exp_pill",
        "product_qty": 1,
        "success_rate": 0.9,
        "min_rank": 1,
        "copper_cost": 30,
        "focus": "炼丹流",
        "stage_hint": "练气-筑基",
        "materials": [
            {"item_id": "herb", "quantity": 2},
        ],
    },
    {
        "id": "recipe_medium_exp",
        "name": "中修为丹",
        "category": "stage_goal",
        "product_item_id": "medium_exp_pill",
        "product_qty": 1,
        "success_rate": 0.8,
        "min_rank": 3,
        "copper_cost": 80,
        "focus": "炼丹流",
        "stage_hint": "练气-筑基",
        "materials": [
            {"item_id": "herb", "quantity": 4},
            {"item_id": "spirit_stone", "quantity": 2},
        ],
    },
    {
        "id": "recipe_large_exp",
        "name": "大修为丹",
        "category": "stage_goal",
        "product_item_id": "large_exp_pill",
        "product_qty": 1,
        "success_rate": 0.6,
        "min_rank": 8,
        "copper_cost": 200,
        "focus": "高阶炼丹流",
        "stage_hint": "金丹-元婴",
        "materials": [
            {"item_id": "spirit_herb", "quantity": 2},
            {"item_id": "spirit_stone", "quantity": 2},
            {"item_id": "immortal_stone", "quantity": 1},
        ],
    },
    {
        "id": "recipe_hp",
        "name": "回血丹",
        "category": "route",
        "product_item_id": "hp_pill",
        "product_qty": 1,
        "success_rate": 0.95,
        "min_rank": 1,
        "copper_cost": 5,
        "focus": "炼丹流",
        "stage_hint": "练气-筑基",
        "materials": [
            {"item_id": "herb", "quantity": 2},
        ],
    },
    {
        "id": "recipe_mp",
        "name": "回蓝丹",
        "category": "route",
        "product_item_id": "mp_pill",
        "product_qty": 1,
        "success_rate": 0.95,
        "min_rank": 1,
        "copper_cost": 10,
        "focus": "炼丹流",
        "stage_hint": "练气-筑基",
        "materials": [
            {"item_id": "herb", "quantity": 2},
        ],
    },
    {
        "id": "recipe_full_restore",
        "name": "大还丹",
        "category": "route",
        "product_item_id": "full_restore_pill",
        "product_qty": 1,
        "success_rate": 0.85,
        "min_rank": 4,
        "copper_cost": 60,
        "focus": "炼丹流",
        "stage_hint": "筑基阶段",
        "materials": [
            {"item_id": "herb", "quantity": 3},
            {"item_id": "spirit_herb", "quantity": 1},
        ],
    },
    {
        "id": "recipe_breakthrough",
        "name": "突破丹",
        "category": "stage_goal",
        "product_item_id": "breakthrough_pill",
        "product_qty": 1,
        "success_rate": 0.9,
        "min_rank": 6,
        "copper_cost": 20,
        "focus": "突破流",
        "stage_hint": "金丹前准备",
        "materials": [
            {"item_id": "spirit_herb", "quantity": 1},
            {"item_id": "demon_core", "quantity": 1},
            {"item_id": "spirit_stone", "quantity": 1},
        ],
    },
    {
        "id": "recipe_breakthrough_adv",
        "name": "高级突破丹",
        "category": "rare",
        "product_item_id": "advanced_breakthrough_pill",
        "product_qty": 1,
        "success_rate": 0.55,
        "min_rank": 12,
        "copper_cost": 300,
        "focus": "突破流",
        "stage_hint": "金丹-元婴",
        "materials": [
            {"item_id": "spirit_herb", "quantity": 2},
            {"item_id": "demon_core", "quantity": 1},
            {"item_id": "immortal_stone", "quantity": 1},
        ],
    },
    {
        "id": "recipe_cultivation_buff",
        "name": "悟道丹",
        "category": "rare",
        "product_item_id": "cultivation_buff_pill",
        "product_qty": 1,
        "success_rate": 0.25,
        "min_rank": 15,
        "copper_cost": 800,
        "focus": "高阶炼丹流",
        "stage_hint": "化神前后",
        "materials": [
            {"item_id": "spirit_herb", "quantity": 3},
            {"item_id": "phoenix_feather", "quantity": 1},
            {"item_id": "immortal_stone", "quantity": 2},
        ],
    },
    {
        "id": "recipe_attack_buff",
        "name": "大力丹",
        "category": "route",
        "product_item_id": "attack_buff_pill",
        "product_qty": 1,
        "success_rate": 0.55,
        "min_rank": 8,
        "copper_cost": 260,
        "focus": "强化路线丹",
        "stage_hint": "金丹-元婴",
        "materials": [
            {"item_id": "iron_ore", "quantity": 4},
            {"item_id": "spirit_stone", "quantity": 2},
            {"item_id": "demon_core", "quantity": 1},
        ],
    },
    {
        "id": "recipe_defense_buff",
        "name": "铁甲丹",
        "category": "route",
        "product_item_id": "defense_buff_pill",
        "product_qty": 1,
        "success_rate": 0.55,
        "min_rank": 8,
        "copper_cost": 260,
        "focus": "护体路线丹",
        "stage_hint": "金丹-元婴",
        "materials": [
            {"item_id": "iron_ore", "quantity": 5},
            {"item_id": "spirit_herb", "quantity": 1},
            {"item_id": "spirit_stone", "quantity": 2},
        ],
    },
    {
        "id": "recipe_cultivation_sprint",
        "name": "修炼冲刺丹",
        "category": "short_term",
        "product_item_id": "cultivation_sprint_pill",
        "product_qty": 1,
        "success_rate": 0.65,
        "min_rank": 5,
        "copper_cost": 200,
        "focus": "短期目标丹",
        "stage_hint": "筑基-金丹",
        "materials": [
            {"item_id": "herb", "quantity": 4},
            {"item_id": "spirit_stone", "quantity": 2},
        ],
    },
    {
        "id": "recipe_realm_drop",
        "name": "秘境掉落丹",
        "category": "short_term",
        "product_item_id": "realm_drop_pill",
        "product_qty": 1,
        "success_rate": 0.6,
        "min_rank": 8,
        "copper_cost": 320,
        "focus": "短期目标丹",
        "stage_hint": "金丹-元婴",
        "materials": [
            {"item_id": "spirit_herb", "quantity": 2},
            {"item_id": "demon_core", "quantity": 1},
        ],
    },
    {
        "id": "recipe_breakthrough_guard",
        "name": "突破保护丹",
        "category": "short_term",
        "product_item_id": "breakthrough_guard_pill",
        "product_qty": 1,
        "success_rate": 0.5,
        "min_rank": 10,
        "copper_cost": 420,
        "focus": "短期目标丹",
        "stage_hint": "金丹-元婴",
        "materials": [
            {"item_id": "spirit_herb", "quantity": 2},
            {"item_id": "demon_core", "quantity": 2},
            {"item_id": "spirit_stone", "quantity": 2},
        ],
    },
    {
        "id": "recipe_void_break",
        "name": "天元护脉丹",
        "category": "rare",
        "product_item_id": "advanced_breakthrough_pill",
        "product_qty": 1,
        "success_rate": 0.48,
        "min_rank": 14,
        "copper_cost": 900,
        "focus": "稀有配方",
        "stage_hint": "元婴以上",
        "materials": [
            {"item_id": "demon_core", "quantity": 2},
            {"item_id": "recipe_fragment", "quantity": 2},
            {"item_id": "immortal_stone", "quantity": 2},
        ],
    },
    {
        "id": "recipe_dragon_soul",
        "name": "龙魂悟道丹",
        "category": "rare",
        "product_item_id": "cultivation_buff_pill",
        "product_qty": 2,
        "success_rate": 0.32,
        "min_rank": 20,
        "copper_cost": 1500,
        "focus": "稀有配方",
        "stage_hint": "化神以上",
        "materials": [
            {"item_id": "dragon_scale", "quantity": 1},
            {"item_id": "phoenix_feather", "quantity": 1},
            {"item_id": "recipe_fragment", "quantity": 3},
            {"item_id": "immortal_stone", "quantity": 3},
        ],
    },
]

ALCHEMY_CATEGORY_LABELS = {
    "stage_goal": "阶段目标丹",
    "route": "路线丹",
    "short_term": "短期目标丹",
    "rare": "稀有配方",
}


def list_recipes(min_rank: int = 1) -> List[Dict[str, Any]]:
    rank = int(min_rank or 1)
    return [r.copy() for r in RECIPES if int(r.get("min_rank", 1) or 1) <= rank]


def get_recipe(recipe_id: str) -> Optional[Dict[str, Any]]:
    for r in RECIPES:
        if r["id"] == recipe_id:
            return r.copy()
    return None


def get_featured_recipe_ids(rank: int) -> List[str]:
    rank = int(rank or 1)
    featured = ["recipe_small_exp", "recipe_hp"]
    if rank >= 4:
        featured.append("recipe_full_restore")
    if rank >= 6:
        featured.append("recipe_breakthrough")
        featured.append("recipe_cultivation_sprint")
    if rank >= 8:
        featured.append("recipe_attack_buff")
        featured.append("recipe_realm_drop")
    if rank >= 10:
        featured.append("recipe_breakthrough_guard")
    if rank >= 12:
        featured.append("recipe_breakthrough_adv")
    if rank >= 14:
        featured.append("recipe_void_break")
    if rank >= 20:
        featured.append("recipe_dragon_soul")
    return featured
