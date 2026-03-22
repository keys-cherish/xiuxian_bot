"""
core/game/herb_garden.py
药园灵植定义、等级配置、时间计算。

移植自 my_farm/game.py，改为修仙风格。
"""

from datetime import datetime, timezone

# ── 灵植配置 ──
# seed_cost / harvest_reward 单位: 下品灵石 (copper)
# growth_minutes: 成长所需分钟数
# type: material / pill_material / rare / legendary
SPIRIT_HERBS = {
    "灵草":       {"emoji": "\U0001f33f", "seed_cost": 3,    "harvest_reward": 8,    "growth_minutes": 30,   "type": "material"},
    "清心草":     {"emoji": "\U0001f331", "seed_cost": 5,    "harvest_reward": 15,   "growth_minutes": 60,   "type": "material"},
    "紫灵花":     {"emoji": "\U0001f49c", "seed_cost": 10,   "harvest_reward": 28,   "growth_minutes": 120,  "type": "material"},
    "火灵果":     {"emoji": "\U0001f525", "seed_cost": 15,   "harvest_reward": 40,   "growth_minutes": 150,  "type": "material"},
    "冰心莲":     {"emoji": "\u2744\ufe0f",  "seed_cost": 20,   "harvest_reward": 52,   "growth_minutes": 180,  "type": "pill_material"},
    "九转灵芝":   {"emoji": "\U0001f344", "seed_cost": 30,   "harvest_reward": 75,   "growth_minutes": 210,  "type": "pill_material"},
    "天雷竹":     {"emoji": "\U0001f38b", "seed_cost": 40,   "harvest_reward": 100,  "growth_minutes": 240,  "type": "material"},
    "凝血草":     {"emoji": "\U0001fa78", "seed_cost": 60,   "harvest_reward": 148,  "growth_minutes": 300,  "type": "pill_material"},
    "养魂木":     {"emoji": "\U0001fab5", "seed_cost": 80,   "harvest_reward": 195,  "growth_minutes": 360,  "type": "material"},
    "千年何首乌": {"emoji": "\U0001f333", "seed_cost": 120,  "harvest_reward": 285,  "growth_minutes": 420,  "type": "pill_material"},
    "龙血果":     {"emoji": "\U0001f409", "seed_cost": 150,  "harvest_reward": 360,  "growth_minutes": 480,  "type": "pill_material"},
    "万年雪莲":   {"emoji": "\U0001f3d4\ufe0f", "seed_cost": 250,  "harvest_reward": 580,  "growth_minutes": 600,  "type": "rare"},
    "太阳神花":   {"emoji": "\U0001f33b", "seed_cost": 500,  "harvest_reward": 1150, "growth_minutes": 720,  "type": "rare"},
    "九幽冥果":   {"emoji": "\U0001f47b", "seed_cost": 1000, "harvest_reward": 2200, "growth_minutes": 960,  "type": "rare"},
    "混沌灵根":   {"emoji": "\u2728",     "seed_cost": 2000, "harvest_reward": 4200, "growth_minutes": 1440, "type": "legendary"},
}

# ── 药园等级配置 ──
# plots: 该等级拥有的田地数量
# exp_next: 升到下一级所需经验
GARDEN_LEVELS = {
    1:  {"plots": 4,  "exp_next": 50},
    2:  {"plots": 5,  "exp_next": 120},
    3:  {"plots": 6,  "exp_next": 250},
    4:  {"plots": 9,  "exp_next": 500},
    5:  {"plots": 10, "exp_next": 800},
    6:  {"plots": 12, "exp_next": 1200},
    7:  {"plots": 14, "exp_next": 1800},
    8:  {"plots": 16, "exp_next": 2500},
    9:  {"plots": 18, "exp_next": 3500},
    10: {"plots": 20, "exp_next": 999999},
}

# ── 虫害与枯萎参数 ──
PEST_CHANCE = 0.08          # 随机虫害概率
PEST_DEATH_MINUTES = 120    # 虫害超时后作物枯死（分钟）
WATER_SPEEDUP_PCT = 0.20    # 浇水加速百分比
WATER_COOLDOWN_SECONDS = 1800  # 浇水冷却 30 分钟

PEST_EVENT_TYPES = [
    ("\U0001f41b", "蛀虫"),
    ("\U0001f4a9", "邪气"),
]

MAX_GARDEN_LEVEL = 10


def get_herb(name: str) -> dict | None:
    """根据名称获取灵植配置。"""
    return SPIRIT_HERBS.get(name)


def get_garden_level_info(level: int) -> dict:
    """获取药园等级信息。"""
    return GARDEN_LEVELS.get(level, GARDEN_LEVELS[MAX_GARDEN_LEVEL])


def list_herb_names() -> list[str]:
    """返回所有灵植名称列表。"""
    return list(SPIRIT_HERBS.keys())


def format_time(minutes: float) -> str:
    """将剩余分钟数格式化为可读字符串。"""
    if minutes <= 0:
        return "已成熟"
    h = int(minutes // 60)
    m = int(minutes % 60)
    if h > 0 and m > 0:
        return f"{h}小时{m}分"
    if h > 0:
        return f"{h}小时"
    return f"{m}分钟"


def format_time_short(minutes: float) -> str:
    """短格式剩余时间（用于网格展示）。"""
    if minutes <= 0:
        return "\u2705"
    h = int(minutes // 60)
    m = int(minutes % 60)
    return f"{h}h{m:02d}"


def get_remaining_minutes(planted_at, growth_minutes: int) -> float:
    """计算剩余生长时间（分钟）。"""
    if not planted_at:
        return -1
    if isinstance(planted_at, str):
        planted_at = datetime.fromisoformat(planted_at)
    if planted_at.tzinfo is None:
        planted_at = planted_at.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    elapsed = (now - planted_at).total_seconds() / 60
    return max(0, growth_minutes - elapsed)


def get_minutes_since_maturity(planted_at, growth_minutes: int) -> float:
    """计算作物成熟后经过的分钟数（用于枯萎判定）。"""
    if not planted_at:
        return -1
    if isinstance(planted_at, str):
        planted_at = datetime.fromisoformat(planted_at)
    if planted_at.tzinfo is None:
        planted_at = planted_at.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    elapsed = (now - planted_at).total_seconds() / 60
    return elapsed - growth_minutes
