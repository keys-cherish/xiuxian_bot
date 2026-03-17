"""
Migrating mechanics, very buggy
"""

from typing import Dict, Any, List, Union

ELEMENTS = ["木", "土", "水", "火", "金"]

# 正确的五行相克关系（A被B克）
# 传统五行: 金克木、木克土、土克水、水克火、火克金
RESTRAINED_ELEMENTS = {
    # "A": "B"     A is restrained by B (A被B克)
    "木": "金",   # 木被金克
    "金": "火",   # 金被火克
    "火": "水",   # 火被水克
    "水": "土",   # 水被土克
    "土": "木",   # 土被木克
}

# 正确的五行相生关系（A生B）
# 传统五行: 金生水、水生木、木生火、火生土、土生金
MUTUAL_ELEMENTS = {
    "金": "水",   # 金生水
    "水": "木",   # 水生木
    "木": "火",   # 木生火
    "火": "土",   # 火生土
    "土": "金",   # 土生金
}

def get_element_relationship(user_element: str, target_element: str) -> str:

    if user_element == target_element:
        return "same"
    elif RESTRAINED_ELEMENTS.get(user_element) == target_element:
        return "restrained"
    elif MUTUAL_ELEMENTS.get(user_element) == target_element:
        return "mutual"
    else:
        return "neutral"

def get_element_multipliers(user_element: str, daily_element: str) -> Dict[str, Union[float, int]]:

    relationship = get_element_relationship(user_element, daily_element)
    
    if relationship == "same":
        return {
            "cul": 1.5,
            "hunt_copper": 2.0,
            "hunt_gold": 2.0,
            "hunt_cultivation": 1.0,
            "asc_fail": 8
        }
    elif relationship == "restrained":
        return {
            "cul": 0.60,
            "hunt_copper": 0.65,
            "hunt_gold": 1.0,
            "hunt_cultivation": 0.60,
            "asc_fail": 18
        }
    elif relationship == "mutual":
        return {
            "cul": 2.5,
            "hunt_copper": 1.8,
            "hunt_gold": 1.5,
            "hunt_cultivation": 2.5,
            "asc_fail": 6
        }
    else:
        return {
            "cul": 1.0,
            "hunt_copper": 1.0,
            "hunt_gold": 1.0,
            "hunt_cultivation": 1.0,
            "asc_fail": 10
        }

def get_element_description(element: str) -> Dict[str, str]:
 
    descriptions = {
        "木": {
            "name_en": "Dendro",
            "name_zh": "木",
            "description_en": "...",
            "description_zh": "..."
        },
        "土": {
            "name_en": "Geo",
            "name_zh": "土",
            "description_en": "...",
            "description_zh": "..."
        },
        "水": {
            "name_en": "Hydro",
            "name_zh": "水",
            "description_en": "...",
            "description_zh": "..."
        },
        "火": {
            "name_en": "Pyro",
            "name_zh": "火",
            "description_en": "...",
            "description_zh": "..."
        },
        "金": {
            "name_en": "Metallo",
            "name_zh": "金",
            "description_en": "...",
            "description_zh": "..."
        }
    }
    
    return descriptions.get(element, {
        "name_en": "Unknown",
        "name_zh": "未知",
        "description_en": "ERROR",
        "description_zh": "ERROR"
    })
