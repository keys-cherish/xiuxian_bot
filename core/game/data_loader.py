"""游戏数据加载器。

从 data/game/ 目录下的 JSON 文件加载游戏数据。
支持缓存和热重载。
"""

import os
import json
import logging
from typing import Any, Dict, List

logger = logging.getLogger("core.data_loader")

_DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "game"
)

_cache: Dict[str, Any] = {}


def load_game_data(filename: str, *, force_reload: bool = False) -> Any:
    """加载游戏数据文件。

    Args:
        filename: 文件名（如 "elements.json"）
        force_reload: 是否强制重新从磁盘读取

    Returns:
        解析后的 JSON 数据
    """
    if not force_reload and filename in _cache:
        return _cache[filename]

    filepath = os.path.join(_DATA_DIR, filename)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        _cache[filename] = data
        return data
    except FileNotFoundError:
        logger.warning(f"Game data file not found: {filepath}")
        return {}
    except json.JSONDecodeError as exc:
        logger.error(f"Invalid JSON in {filepath}: {exc}")
        return {}


def reload_all() -> None:
    """清除缓存，强制重新加载所有数据。"""
    _cache.clear()
    logger.info("Game data cache cleared")


# ---- 便捷访问函数 ----

def get_elements_data() -> Dict[str, Any]:
    return load_game_data("elements.json")


def get_realms_data() -> List:
    return load_game_data("realms.json")


def get_monsters_data() -> List:
    return load_game_data("monsters.json")


def get_skills_data() -> List:
    return load_game_data("skills.json")


def get_items_data() -> Dict[str, Any]:
    return load_game_data("items.json")


def get_shop_data() -> List:
    return load_game_data("shop.json")


def get_quests_data() -> List:
    return load_game_data("quests.json")


def get_secret_realms_data() -> List:
    return load_game_data("secret_realms.json")
