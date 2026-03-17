"""
NPC 系统 - 角色定义与记忆系统
"""

from typing import Dict, Any, Optional, List
from enum import Enum


class NPCDisposition(Enum):
    HOSTILE = "hostile"
    COLD = "cold"
    NEUTRAL = "neutral"
    FRIENDLY = "friendly"
    CLOSE = "close"


# 好感度 → 态度映射
AFFINITY_THRESHOLDS = [
    (-100, -50, NPCDisposition.HOSTILE, "仇敌"),
    (-50, -10, NPCDisposition.COLD, "冷漠"),
    (-10, 20, NPCDisposition.NEUTRAL, "陌生人"),
    (20, 60, NPCDisposition.FRIENDLY, "还算不错的道友"),
    (60, 100, NPCDisposition.CLOSE, "至交好友"),
]


# NPC 定义列表 - 至少20个NPC分布在各地图
NPCS = [
    # === 苍澜城 NPC ===
    {
        "id": "old_beggar",
        "name": "老乞丐",
        "title": "神秘老人",
        "location": "canglan_city",
        "type": "story",  # story/merchant/quest/trainer/random
        "personality": "看似疯癫实则高深莫测",
        "initial_dialogue": "呵呵，小家伙，你身上有股不寻常的气息...",
        "dao_path": "heng",
        "realm_hint": 32,  # 暗示是高境界隐世高手
        "quests": ["find_jade_pendant"],
        "trades": [],
    },
    {
        "id": "merchant_wang",
        "name": "王掌柜",
        "title": "万宝楼苍澜分店掌柜",
        "location": "canglan_city",
        "type": "merchant",
        "personality": "精明圆滑但讲信誉",
        "initial_dialogue": "这位道友，万宝楼童叟无欺，看看有什么需要的？",
        "trades": ["basic_pills", "basic_materials"],
        "quests": ["delivery_task"],
    },
    {
        "id": "herb_girl",
        "name": "药灵儿",
        "title": "采药少女",
        "location": "canglan_city",
        "type": "quest",
        "personality": "天真活泼",
        "initial_dialogue": "道友好！你要买灵草吗？我采的灵草可是最新鲜的！",
        "dao_path": None,
        "quests": ["gather_herbs", "protect_herb_girl"],
        "trades": ["herbs"],
    },
    # 东郊灵林
    {
        "id": "forest_hermit",
        "name": "林中老人",
        "title": "隐修散人",
        "location": "east_forest",
        "type": "trainer",
        "personality": "沉默寡言但热心教导",
        "initial_dialogue": "嗯？你也来此处修炼？",
        "dao_path": "heng",
        "teaches": ["taiqing_yangqi"],  # 可教功法
    },
    {
        "id": "hunter_zhang",
        "name": "猎户张大",
        "title": "灵兽猎人",
        "location": "east_forest",
        "type": "quest",
        "personality": "豪爽直率",
        "initial_dialogue": "兄弟！今天的林子不太平，一起走？",
        "quests": ["clear_beasts"],
    },
    # 南市坊市
    {
        "id": "blacksmith_liu",
        "name": "刘铁匠",
        "title": "器道师傅",
        "location": "south_market",
        "type": "merchant",
        "personality": "暴脾气但手艺精湛",
        "initial_dialogue": "别磨蹭！要打什么器？说！",
        "trades": ["weapons", "armor"],
    },
    {
        "id": "fortune_teller",
        "name": "瞎眼老妪",
        "title": "算命婆婆",
        "location": "south_market",
        "type": "story",
        "personality": "神秘兮兮，说话半真半假",
        "initial_dialogue": "哎呦...你这命格...有意思...",
        "quests": ["fortune_quest"],
    },
    # 北望灵山
    {
        "id": "taiqing_elder",
        "name": "太清长老",
        "title": "太清宗驻山长老",
        "location": "north_mountain",
        "type": "trainer",
        "personality": "严厉但公正",
        "initial_dialogue": "此处乃太清宗修炼之地，闲杂人等不得入内。你...倒有些根骨。",
        "dao_path": "heng",
        "teaches": ["chunyang_wuji", "hunyuan_dadao"],
    },
    # 落霞谷
    {
        "id": "pill_master_chen",
        "name": "陈丹师",
        "title": "丹鼎阁驻谷丹师",
        "location": "luoxia_valley",
        "type": "merchant",
        "personality": "学究气重，痴迷炼丹",
        "initial_dialogue": "嘘！别吵...我这炉丹快成了...",
        "trades": ["pills"],
    },
    # 瘴气沼泽
    {
        "id": "swamp_witch",
        "name": "沼泽女巫",
        "title": "万鬼门弃徒",
        "location": "misty_swamp",
        "type": "quest",
        "personality": "阴险但遵守交易",
        "initial_dialogue": "嘻嘻...来到这里的人，要么是迷路了，要么是找死。你是哪种？",
        "dao_path": "ni",
        "quests": ["swamp_collection"],
    },
    # 天渊宗城 (筑基后解锁)
    {
        "id": "tianyuan_gatekeeper",
        "name": "守山弟子",
        "title": "天渊宗看门弟子",
        "location": "tianyuan_sect_city",
        "type": "quest",
        "personality": "尽职尽责略显拘谨",
        "initial_dialogue": "请出示令牌...哦，是新来的道友？",
    },
    {
        "id": "sword_master_li",
        "name": "李剑仙",
        "title": "天剑门掌门",
        "location": "sword_peak",
        "type": "trainer",
        "personality": "冷傲但惜才",
        "initial_dialogue": "...",
        "dao_path": "heng",
        "teaches": ["sword_arts"],
    },
    {
        "id": "pill_pavilion_master",
        "name": "丹阁主",
        "title": "丹鼎阁阁主",
        "location": "pill_pavilion",
        "type": "merchant",
        "personality": "温文尔雅，商人本色",
        "trades": ["rare_pills", "recipes"],
    },
    {
        "id": "star_elder",
        "name": "星辰长老",
        "title": "星辰阁隐世长老",
        "location": "star_fall_sea",
        "type": "trainer",
        "personality": "超然物外，看透一切",
        "dao_path": "yan",
        "teaches": ["xingchen_bian", "wanxiang_xinghe"],
    },
    {
        "id": "reverse_dao_master",
        "name": "逆道老人",
        "title": "逆天殿长老",
        "location": "reverse_land",
        "type": "trainer",
        "personality": "偏执但信念坚定",
        "dao_path": "ni",
        "teaches": ["ni_tian_jue", "shengsi_yin"],
    },
    # 灵界(占位)
    {
        "id": "immortal_alliance_envoy",
        "name": "仙盟使者",
        "title": "灵界仙盟迎新使",
        "location": "tianling_domain",
        "type": "story",
        "personality": "公事公办",
        "initial_dialogue": "新飞升的修士？登记在册。",
    },
    # 额外4个补足20
    {
        "id": "wine_monk",
        "name": "酒和尚",
        "title": "醉酒僧人",
        "location": "canglan_city",
        "type": "random",
        "personality": "嗜酒如命，偶尔醒来说出惊人之语",
        "initial_dialogue": "嗝...你...你有酒吗？",
    },
    {
        "id": "mining_foreman",
        "name": "矿头老赵",
        "title": "苍澜矿脉工头",
        "location": "canglan_mines",
        "type": "quest",
        "personality": "粗犷实在",
        "initial_dialogue": "来挖矿？好！多个人手！",
        "quests": ["mine_quest"],
    },
    {
        "id": "lake_spirit",
        "name": "湖灵",
        "title": "坠星湖守护灵",
        "location": "fallen_star_lake",
        "type": "story",
        "personality": "空灵缥缈",
        "initial_dialogue": "你...也是被星辰指引而来的吗？",
    },
    {
        "id": "chaos_sea_pirate",
        "name": "海盗头子",
        "title": "乱星海散修盟主",
        "location": "chaos_sea",
        "type": "merchant",
        "personality": "江湖义气",
        "initial_dialogue": "哈哈！乱星海不问出身，只问本事！",
        "trades": ["black_market"],
    },
]

# 按 id 建索引，方便 O(1) 查找
_NPC_INDEX: Dict[str, Dict[str, Any]] = {n["id"]: n for n in NPCS}

# 按地图 id 分组
_NPC_BY_LOCATION: Dict[str, List[Dict[str, Any]]] = {}
for _npc in NPCS:
    _NPC_BY_LOCATION.setdefault(_npc["location"], []).append(_npc)


# ── 互动类型 → 好感变化基础值 ──
_INTERACTION_AFFINITY: Dict[str, int] = {
    "chat": 1,
    "gift_common": 3,
    "gift_rare": 8,
    "gift_legendary": 15,
    "quest_complete": 10,
    "trade": 2,
    "insult": -10,
    "attack": -25,
    "help_combat": 5,
}


def get_npc(npc_id: str) -> Optional[Dict[str, Any]]:
    """按 id 获取 NPC 定义，不存在返回 None"""
    return _NPC_INDEX.get(npc_id)


def get_npcs_by_location(map_id: str) -> List[Dict[str, Any]]:
    """获取指定地图上的所有 NPC，无则返回空列表"""
    return _NPC_BY_LOCATION.get(map_id, [])


def get_impression(affinity: int) -> str:
    """好感度数值转换为印象文本（中文描述）"""
    for low, high, _disposition, label in AFFINITY_THRESHOLDS:
        if low <= affinity < high:
            return label
    # 超出上限视为至交，低于下限视为仇敌
    if affinity >= 100:
        return "至交好友"
    return "仇敌"


def calc_affinity_change(interaction_type: str) -> int:
    """根据互动类型返回好感度基础变化值，未知类型返回 0"""
    return _INTERACTION_AFFINITY.get(interaction_type, 0)
