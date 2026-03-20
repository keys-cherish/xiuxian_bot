"""
万级随机事件批量生成器
按分类矩阵(category x sub_category x realm_range x rarity)生成事件骨架
输出 SQL INSERT 语句，直接导入 PostgreSQL

用法: python scripts/generate_events.py > output.sql
"""
import itertools
import random
import json

# ============================================================
# 分类矩阵定义
# ============================================================

CATEGORIES = {
    "combat": {
        "subs": [
            ("beast",             "forest",   "妖兽遭遇", "combat/beast_encounter"),
            ("beast_mountain",    "mountain", "山地妖兽", "combat/beast_encounter"),
            ("beast_plain",       "plain",    "荒原妖兽", "combat/beast_encounter"),
            ("beast_cave",        "cave",     "洞穴妖兽", "combat/beast_encounter"),
            ("beast_swamp",       "swamp",    "沼泽妖兽", "combat/beast_encounter"),
            ("evil_cultivator",   None,       "邪修对决", "combat/evil_cultivator"),
            ("evil_poison",       "forest",   "毒蛊邪修", "combat/evil_cultivator"),
            ("evil_blood",        None,       "血修围杀", "combat/evil_cultivator"),
            ("sect_hunter",       None,       "宗门猎杀", "combat/evil_cultivator"),
            ("ambush_road",       "road",     "路途伏击", "combat/ambush"),
            ("ambush_formation",  "ruin",     "阵法陷阱", "combat/ambush"),
            ("ambush_night",      "camp",     "夜袭营地", "combat/ambush"),
            ("tribulation_beast", None,       "雷劫兽",   "combat/tribulation_beast"),
            ("heart_demon",       None,       "心魔化形", "combat/tribulation_beast"),
            ("sparring",          "sect",     "宗门切磋", "combat/beast_encounter"),
            ("arena",             "market",   "擂台赛",   "combat/beast_encounter"),
            ("bounty_target",     None,       "悬赏目标", "combat/evil_cultivator"),
            ("guard_beast",       "ruin",     "守关妖兽", "combat/beast_encounter"),
            ("puppet",            "ruin",     "傀儡卫士", "combat/ambush"),
        ],
        "realm_ranges": [(1,4),(2,6),(3,8),(5,10),(7,14),(10,18),(14,22),(18,26),(22,30),(26,32)],
    },
    "adventure": {
        "subs": [
            ("cave_spring",       "mountain", "灵泉洞府", "adventure/ancient_cave"),
            ("cave_bone",         "desert",   "枯骨秘藏", "adventure/ancient_cave"),
            ("cave_time",         None,       "时空裂隙", "adventure/ancient_cave"),
            ("cave_crystal",      "cave",     "灵晶矿洞", "adventure/ancient_cave"),
            ("cave_ice",          "mountain", "冰封地宫", "adventure/ancient_cave"),
            ("secret_star",       None,       "星陨秘境", "adventure/secret_realm"),
            ("secret_battlefield",None,       "古战场",   "adventure/secret_realm"),
            ("secret_dream",      None,       "梦境试炼", "adventure/secret_realm"),
            ("secret_fire",       "mountain", "火山秘境", "adventure/secret_realm"),
            ("meteorite_fall",    None,       "流星坠落", "adventure/meteorite"),
            ("meteorite_beast",   "mountain", "星力异兽", "adventure/meteorite"),
            ("meteorite_mine",    "plain",    "陨铁矿脉", "adventure/meteorite"),
            ("immortal_manor",    "mountain", "仙人遗府", "adventure/fallen_immortal"),
            ("immortal_ghost",    None,       "仙人残灵", "adventure/fallen_immortal"),
            ("immortal_array",    "ruin",     "仙阵遗迹", "adventure/fallen_immortal"),
            ("treasure_map",      None,       "藏宝图",   "adventure/ancient_cave"),
            ("herb_garden",       "forest",   "灵药园",   "adventure/ancient_cave"),
            ("ruin_explore",      "ruin",     "废墟探索", "adventure/ancient_cave"),
            ("underwater_palace", "water",    "水底宫殿", "adventure/secret_realm"),
            ("cloud_realm",       "mountain", "云上秘境", "adventure/secret_realm"),
        ],
        "realm_ranges": [(1,5),(2,7),(3,9),(5,12),(8,16),(12,20),(16,24),(20,28),(24,32)],
    },
    "social": {
        "subs": [
            ("market_vendor",    "market", "神秘摊贩", "social/market_trade"),
            ("market_auction",   "market", "拍卖奇遇", "social/market_trade"),
            ("market_merchant",  "road",   "行脚商人", "social/market_trade"),
            ("market_haggle",    "market", "讨价还价", "social/market_trade"),
            ("sect_resource",    "sect",   "资源争夺", "social/sect_conflict"),
            ("sect_politics",    "sect",   "内门纷争", "social/sect_conflict"),
            ("sect_challenge",   None,     "门派切磋", "social/sect_conflict"),
            ("sect_mission",     "sect",   "宗门任务", "social/sect_conflict"),
            ("romance_meet",     None,     "偶遇",     "social/romance"),
            ("romance_help",     None,     "共渡危机", "social/romance"),
            ("romance_bond",     None,     "羁绊加深", "social/romance"),
            ("npc_elder",        "sect",   "长老教诲", "social/sect_conflict"),
            ("npc_disciple",     "sect",   "同门互动", "social/sect_conflict"),
            ("npc_wanderer",     "road",   "游方散修", "social/market_trade"),
            ("npc_healer",       "market", "药师问诊", "social/market_trade"),
        ],
        "realm_ranges": [(1,5),(2,8),(4,12),(8,18),(14,24),(20,32)],
    },
    "enlightenment": {
        "subs": [
            ("meditation_calm",   None,     "平静冥想", "enlightenment/breakthrough"),
            ("meditation_deep",   None,     "深度入定", "enlightenment/breakthrough"),
            ("insight_sword",     None,     "剑道感悟", "enlightenment/breakthrough"),
            ("insight_pill",      None,     "丹道感悟", "enlightenment/breakthrough"),
            ("insight_array",     None,     "阵法感悟", "enlightenment/breakthrough"),
            ("insight_nature",    "forest", "自然感悟", "enlightenment/breakthrough"),
            ("breakthrough_minor",None,     "小境界突破","enlightenment/breakthrough"),
            ("breakthrough_major",None,     "大境界突破","enlightenment/breakthrough"),
            ("dao_heng",          None,     "恒道感悟", "enlightenment/breakthrough"),
            ("dao_ni",            None,     "逆道感悟", "enlightenment/breakthrough"),
            ("dao_yan",           None,     "衍道感悟", "enlightenment/breakthrough"),
            ("ancient_text",      "ruin",   "古籍残篇", "enlightenment/breakthrough"),
        ],
        "realm_ranges": [(1,6),(3,10),(6,16),(10,22),(16,28),(22,32)],
    },
    "tribulation": {
        "subs": [
            ("thunder_1",  None, "雷劫初临", "tribulation/lightning"),
            ("thunder_3",  None, "三重雷劫", "tribulation/lightning"),
            ("thunder_9",  None, "九重雷劫", "tribulation/lightning"),
            ("fire_trib",  None, "火劫焚身", "tribulation/lightning"),
            ("wind_trib",  None, "风劫裂体", "tribulation/lightning"),
            ("heart_trib", None, "心魔劫",   "tribulation/lightning"),
        ],
        "realm_ranges": [(8,14),(10,18),(14,22),(18,26),(22,30),(26,32)],
    },
    "karma": {
        "subs": [
            ("good_help",     None,    "出手相助", "karma/deeds"),
            ("good_mercy",    None,    "手下留情", "karma/deeds"),
            ("good_charity",  "market","散财济困", "karma/deeds"),
            ("bad_kill",      None,    "杀孽缠身", "karma/deeds"),
            ("bad_betray",    None,    "背信弃义", "karma/deeds"),
            ("bad_greed",     None,    "贪念入心", "karma/deeds"),
            ("effect_positive",None,   "善果回馈", "karma/deeds"),
            ("effect_negative",None,   "业报清算", "karma/deeds"),
            ("past_life",     None,    "前世因缘", "karma/deeds"),
        ],
        "realm_ranges": [(1,8),(3,14),(6,20),(12,26),(18,32)],
    },
    "daily": {
        "subs": [
            ("morning_train",  None,    "晨练", "daily/activities"),
            ("alchemy_work",   "sect",  "炼丹", "daily/activities"),
            ("market_browse",  "market","逛坊市","daily/activities"),
            ("rest_read",      None,    "读书", "daily/activities"),
            ("rest_social",    "sect",  "闲聊", "daily/activities"),
            ("craft_forge",    "sect",  "锻造", "daily/activities"),
            ("gather_herb",    "forest","采药", "daily/activities"),
            ("gather_mine",    "mountain","采矿","daily/activities"),
            ("gather_fish",    "water", "钓鱼", "daily/activities"),
        ],
        "realm_ranges": [(1,5),(2,8),(4,14),(8,20),(14,28),(20,32)],
    },
}

RARITIES_AND_WEIGHTS = [
    ("common",    1.0,  0.35),  # (rarity, base_weight, proportion)
    ("uncommon",  0.7,  0.25),
    ("rare",      0.4,  0.20),
    ("epic",      0.15, 0.12),
    ("legendary", 0.06, 0.06),
    ("mythic",    0.02, 0.02),
]

# ============================================================
# 蝴蝶标签生成
# ============================================================

TAG_POOL_BY_CATEGORY = {
    "combat":       ["初斗妖兽","狼妖老手","斩蛇之人","雷翎猎手","血影追踪","遇袭幸存","破阵专家","渡劫感悟","心魔斩断","妖兽潮幸存者"],
    "adventure":    ["灵泉记忆","枯骨玉佩","时空裂隙","星陨入场","星力觉醒","仙府缘起","仙人遗愿","星辰传人","古战场历练者"],
    "social":       ["神秘摊贩相遇","宗门争端","内门靠山","道侣相遇","羁绊深化"],
    "enlightenment":["顿悟者","境界精通","大道先行者"],
    "tribulation":  ["渡劫在望","渡劫幸存","雷劫超度者"],
    "karma":        ["善缘+1","业障+1","功德积累","业障深重","天道眷顾","业报清算"],
    "daily":        [],
}

def gen_tags(cat: str) -> str:
    pool = TAG_POOL_BY_CATEGORY.get(cat, [])
    if not pool:
        return "[]"
    # 30% 概率产出 1 个标签
    if random.random() < 0.3 and pool:
        return json.dumps([random.choice(pool)], ensure_ascii=False)
    return "[]"

def gen_required_tags(cat: str, rarity: str) -> str:
    if rarity in ("common", "uncommon"):
        return "[]"
    pool = TAG_POOL_BY_CATEGORY.get(cat, [])
    if not pool:
        return "[]"
    # epic+ 有 40% 概率要求前置标签
    if random.random() < 0.4:
        return json.dumps([random.choice(pool)], ensure_ascii=False)
    return "[]"

# ============================================================
# 生成
# ============================================================

def generate_all():
    event_id_counter = {}
    all_events = []

    for cat, cfg in CATEGORIES.items():
        subs = cfg["subs"]
        realm_ranges = cfg["realm_ranges"]
        cat_prefix = cat[:3].upper()

        for sub_tuple in subs:
            sub_id, location_type, sub_name, template_base = sub_tuple
            sub_prefix = sub_id[:8].upper().replace("_","")

            for realm_min, realm_max in realm_ranges:
                for rarity, base_weight, proportion in RARITIES_AND_WEIGHTS:
                    # 控制生成数量：common 多，mythic 少
                    count = max(1, int(proportion * 3))
                    if rarity in ("legendary", "mythic"):
                        count = 1

                    for i in range(count):
                        key = f"{cat_prefix}_{sub_prefix}"
                        event_id_counter[key] = event_id_counter.get(key, 0) + 1
                        eid = f"{key}_{event_id_counter[key]:04d}"

                        # 构建 template_key
                        template_key = f"{template_base}::{sub_id}"

                        # cooldown
                        cd_map = {"common":8,"uncommon":12,"rare":20,"epic":35,"legendary":50,"mythic":80}
                        cooldown = cd_map.get(rarity, 10)

                        produced_tags = gen_tags(cat)
                        required_tags = gen_required_tags(cat, rarity)

                        loc = f"'{location_type}'" if location_type else "NULL"

                        all_events.append(
                            f"('{eid}','{cat}','{sub_id}','{rarity}',"
                            f"{realm_min},{realm_max},{loc},"
                            f"'{template_key}',{base_weight:.2f},{cooldown},"
                            f"'{required_tags}','[]','{produced_tags}',"
                            f"FALSE,NULL,NULL,NOW())"
                        )

    return all_events

def main():
    events = generate_all()
    print(f"-- Auto-generated {len(events)} events")
    print("-- Run: psql -d xianxia -f this_file.sql")
    print()
    print("BEGIN;")
    print()

    # 分批 INSERT（每批 500 条）
    batch_size = 500
    for i in range(0, len(events), batch_size):
        batch = events[i:i+batch_size]
        print("INSERT INTO events (event_id,category,sub_category,rarity,")
        print("  realm_min,realm_max,location_type,template_key,base_weight,")
        print("  cooldown_events,required_tags,excluded_tags,produced_tags,")
        print("  is_chain_event,chain_id,chain_stage,created_at)")
        print("VALUES")
        print(",\n".join(batch))
        print("ON CONFLICT (event_id) DO NOTHING;")
        print()

    print("COMMIT;")
    print(f"-- Total: {len(events)} events generated")

if __name__ == "__main__":
    main()
