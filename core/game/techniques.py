"""
功法体系 - Cultivation Technique System

与 skills.py（战斗技能）独立，本模块定义修炼功法、丹药品级、法宝品级等。
功法影响修炼速度、突破成功率、三道亲和度，是角色成长的核心选择。
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, Any, List, Optional


# ---------------------------------------------------------------------------
# 品级枚举
# ---------------------------------------------------------------------------

class TechniqueGrade(Enum):
    """功法大品级"""
    FAN = "fan"            # 凡级
    LING = "ling"          # 灵级
    XIAN = "xian"          # 仙级
    SHEN = "shen"          # 神级
    ZAOHUA = "zaohua"      # 造化级
    HONGMENG = "hongmeng"  # 鸿蒙级


class TechniqueSubGrade(Enum):
    """功法子品级（造化/鸿蒙为 UNIQUE）"""
    XIA = "xia"        # 下
    ZHONG = "zhong"    # 中
    SHANG = "shang"    # 上
    JI = "ji"          # 极
    UNIQUE = "unique"  # 无品（造化/鸿蒙专用）


# 品级排序权重，用于比较两部功法的品阶高低
GRADE_ORDER: Dict[str, int] = {
    "fan": 0,
    "ling": 1,
    "xian": 2,
    "shen": 3,
    "zaohua": 4,
    "hongmeng": 5,
}

SUB_GRADE_ORDER: Dict[str, int] = {
    "xia": 0,
    "zhong": 1,
    "shang": 2,
    "ji": 3,
    "unique": 4,
}

# 品级中文映射
GRADE_CN: Dict[str, str] = {
    "fan": "凡级",
    "ling": "灵级",
    "xian": "仙级",
    "shen": "神级",
    "zaohua": "造化级",
    "hongmeng": "鸿蒙级",
}

SUB_GRADE_CN: Dict[str, str] = {
    "xia": "下品",
    "zhong": "中品",
    "shang": "上品",
    "ji": "极品",
    "unique": "",
}


# ---------------------------------------------------------------------------
# 三道分类
# ---------------------------------------------------------------------------

DAO_PATHS = {
    "heng": "恒道",   # 顺天应道，稳健长生
    "ni": "逆道",     # 逆天改命，险中求胜
    "yan": "衍道",    # 万法衍生，变化无穷
    "misc": "兼修/旁门",  # 不属于三大主道的旁门功法
}


# ---------------------------------------------------------------------------
# 法宝品级
# ---------------------------------------------------------------------------

ARTIFACT_GRADES = [
    "凡器",
    "灵器",
    "法宝",
    "灵宝",
    "仙器",
    "神器",
    "造化至宝",
    "鸿蒙圣物",
]


# ---------------------------------------------------------------------------
# 核心功法列表
# ---------------------------------------------------------------------------
# min_realm / max_realm 对应 realms.py 中 REALMS[*]["id"]
#   1=凡人, 2-5=练气, 6-9=筑基, 10-13=金丹, 14-17=元婴,
#   18-21=化神, 22-25=炼虚, 26-29=合体, 30=大乘, 31=渡劫, 32=真仙

TECHNIQUES: List[Dict[str, Any]] = [
    # ========================= 恒道系列 =========================
    {
        "id": "taiqing_yangqi",
        "name": "太清养气诀",
        "dao_path": "heng",
        "grade": TechniqueGrade.FAN,
        "sub_grade": TechniqueSubGrade.SHANG,
        "min_realm": 1,
        "max_realm": 5,
        "exp_multiplier": 1.0,
        "dao_gain": {"heng": 2},
        "breakthrough_bonus": 0.0,
        "combat_bonus": {},
        "special": "",
        "desc": "修真入门功法，温和平稳，适合所有灵根",
        "cost_spirit_stones": 0,
    },
    {
        "id": "chunyang_wuji",
        "name": "纯阳无极功",
        "dao_path": "heng",
        "grade": TechniqueGrade.FAN,
        "sub_grade": TechniqueSubGrade.JI,
        "min_realm": 6,
        "max_realm": 17,
        "exp_multiplier": 1.3,
        "dao_gain": {"heng": 4},
        "breakthrough_bonus": 0.02,
        "combat_bonus": {"attack_pct": 0.05, "defense_pct": 0.03},
        "special": "阳属性灵根额外修炼加速10%",
        "desc": "至阳至刚的正统功法，筑基至元婴阶段首选",
        "cost_spirit_stones": 500,
    },
    {
        "id": "hunyuan_dadao",
        "name": "混元大道经",
        "dao_path": "heng",
        "grade": TechniqueGrade.LING,
        "sub_grade": TechniqueSubGrade.SHANG,
        "min_realm": 18,
        "max_realm": 29,
        "exp_multiplier": 1.8,
        "dao_gain": {"heng": 8},
        "breakthrough_bonus": 0.03,
        "combat_bonus": {"attack_pct": 0.08, "defense_pct": 0.08, "hp_pct": 0.05},
        "special": "化神以上突破时额外恢复10%修为",
        "desc": "混元一气，道法自然。化神至合体阶段的恒道正统",
        "cost_spirit_stones": 50000,
    },
    {
        "id": "taichu_xianjing",
        "name": "太初仙经",
        "dao_path": "heng",
        "grade": TechniqueGrade.XIAN,
        "sub_grade": TechniqueSubGrade.SHANG,
        "min_realm": 30,
        "max_realm": 32,
        "exp_multiplier": 2.5,
        "dao_gain": {"heng": 15},
        "breakthrough_bonus": 0.05,
        "combat_bonus": {"attack_pct": 0.12, "defense_pct": 0.10, "hp_pct": 0.10},
        "special": "领悟时间法则碎片，战斗中有5%概率触发时间减速",
        "desc": "太初无形，道生万物。真仙级恒道仙经，蕴含时间法则",
        "cost_spirit_stones": 5000000,
    },
    {
        "id": "hengdao_tianshu_shang",
        "name": "恒道天书·上卷",
        "dao_path": "heng",
        "grade": TechniqueGrade.HONGMENG,
        "sub_grade": TechniqueSubGrade.UNIQUE,
        "min_realm": 32,
        "max_realm": 32,
        "exp_multiplier": 5.0,
        "dao_gain": {"heng": 50},
        "breakthrough_bonus": 0.10,
        "combat_bonus": {"attack_pct": 0.25, "defense_pct": 0.25, "hp_pct": 0.20},
        "special": "鸿蒙之力：战斗中每回合恢复2%生命，免疫控制效果",
        "desc": "三大天书之一，记载恒道终极奥义",
        "cost_spirit_stones": 0,  # 不可购买，仅机缘获得
    },

    # ========================= 逆道系列 =========================
    {
        "id": "ni_tian_jue",
        "name": "逆天诀",
        "dao_path": "ni",
        "grade": TechniqueGrade.FAN,
        "sub_grade": TechniqueSubGrade.SHANG,
        "min_realm": 1,
        "max_realm": 9,
        "exp_multiplier": 1.2,
        "dao_gain": {"ni": 3},
        "breakthrough_bonus": -0.02,
        "combat_bonus": {"attack_pct": 0.08},
        "special": "修炼有5%概率触发走火入魔，损失少量修为但攻击永久+1%",
        "desc": "逆道入门，以战养战，高风险高收益",
        "cost_spirit_stones": 100,
    },
    {
        "id": "shengsi_yin",
        "name": "生死印",
        "dao_path": "ni",
        "grade": TechniqueGrade.LING,
        "sub_grade": TechniqueSubGrade.ZHONG,
        "min_realm": 14,
        "max_realm": 21,
        "exp_multiplier": 1.6,
        "dao_gain": {"ni": 7},
        "breakthrough_bonus": -0.01,
        "combat_bonus": {"attack_pct": 0.12, "crit_rate": 0.05},
        "special": "击杀敌人回复15%生命；血量低于30%时攻击+20%",
        "desc": "生死之间领悟大道，元婴级逆道秘法",
        "cost_spirit_stones": 30000,
    },
    {
        "id": "lunhui_tianjing",
        "name": "轮回天经",
        "dao_path": "ni",
        "grade": TechniqueGrade.XIAN,
        "sub_grade": TechniqueSubGrade.ZHONG,
        "min_realm": 18,
        "max_realm": 30,
        "exp_multiplier": 2.2,
        "dao_gain": {"ni": 12},
        "breakthrough_bonus": 0.0,
        "combat_bonus": {"attack_pct": 0.15, "crit_rate": 0.08, "crit_damage": 0.15},
        "special": "死亡后有10%概率原地复活（每场战斗限一次）",
        "desc": "轮回不灭，生死轮转。化神至大乘的逆道至高经文",
        "cost_spirit_stones": 500000,
    },
    {
        "id": "pomie_xianjue",
        "name": "破灭仙诀",
        "dao_path": "ni",
        "grade": TechniqueGrade.XIAN,
        "sub_grade": TechniqueSubGrade.JI,
        "min_realm": 31,
        "max_realm": 32,
        "exp_multiplier": 2.8,
        "dao_gain": {"ni": 18},
        "breakthrough_bonus": 0.04,
        "combat_bonus": {"attack_pct": 0.20, "crit_rate": 0.10, "crit_damage": 0.20},
        "special": "无视目标10%防御；攻击附带破灭之力，降低治疗效果50%",
        "desc": "一念破灭万法，真仙级逆道绝学",
        "cost_spirit_stones": 8000000,
    },
    {
        "id": "nidao_tianshu_zhong",
        "name": "逆道天书·中卷",
        "dao_path": "ni",
        "grade": TechniqueGrade.HONGMENG,
        "sub_grade": TechniqueSubGrade.UNIQUE,
        "min_realm": 32,
        "max_realm": 32,
        "exp_multiplier": 5.0,
        "dao_gain": {"ni": 50},
        "breakthrough_bonus": 0.10,
        "combat_bonus": {"attack_pct": 0.35, "crit_rate": 0.15, "crit_damage": 0.30},
        "special": "鸿蒙之力：攻击无视20%防御，每次暴击回复5%血量",
        "desc": "三大天书之二，记载逆道终极奥义",
        "cost_spirit_stones": 0,
    },

    # ========================= 衍道系列 =========================
    {
        "id": "xingchen_bian",
        "name": "星辰变",
        "dao_path": "yan",
        "grade": TechniqueGrade.FAN,
        "sub_grade": TechniqueSubGrade.JI,
        "min_realm": 1,
        "max_realm": 9,
        "exp_multiplier": 1.1,
        "dao_gain": {"yan": 3},
        "breakthrough_bonus": 0.01,
        "combat_bonus": {"hp_pct": 0.08, "defense_pct": 0.05},
        "special": "兼修炼体，物理伤害减免额外+3%",
        "desc": "炼体入道，以肉身演化星辰万象",
        "cost_spirit_stones": 200,
    },
    {
        "id": "wanxiang_xinghe",
        "name": "万象星河决",
        "dao_path": "yan",
        "grade": TechniqueGrade.LING,
        "sub_grade": TechniqueSubGrade.SHANG,
        "min_realm": 14,
        "max_realm": 25,
        "exp_multiplier": 1.7,
        "dao_gain": {"yan": 8},
        "breakthrough_bonus": 0.02,
        "combat_bonus": {"attack_pct": 0.06, "defense_pct": 0.06, "hp_pct": 0.06},
        "special": "随机强化：每次战斗开始随机提升一项属性15%",
        "desc": "星河万象，变化无穷。元婴级衍道正典",
        "cost_spirit_stones": 40000,
    },
    {
        "id": "zaohua_shenjue",
        "name": "造化神诀",
        "dao_path": "yan",
        "grade": TechniqueGrade.SHEN,
        "sub_grade": TechniqueSubGrade.ZHONG,
        "min_realm": 30,
        "max_realm": 32,
        "exp_multiplier": 3.0,
        "dao_gain": {"yan": 20},
        "breakthrough_bonus": 0.05,
        "combat_bonus": {"attack_pct": 0.15, "defense_pct": 0.12, "hp_pct": 0.12},
        "special": "造化之力：战斗中每3回合随机召唤一个元素分身",
        "desc": "造化弄人，亦可由人造化。仙王级衍道至高秘典",
        "cost_spirit_stones": 10000000,
    },
    {
        "id": "hongmeng_zaohua",
        "name": "鸿蒙造化诀",
        "dao_path": "yan",
        "grade": TechniqueGrade.SHEN,
        "sub_grade": TechniqueSubGrade.JI,
        "min_realm": 32,
        "max_realm": 32,
        "exp_multiplier": 4.0,
        "dao_gain": {"yan": 35},
        "breakthrough_bonus": 0.08,
        "combat_bonus": {"attack_pct": 0.20, "defense_pct": 0.18, "hp_pct": 0.15},
        "special": "鸿蒙造化同源，丹药/炼器成功率+15%",
        "desc": "鸿蒙初开，造化为尊。神主级衍道功法",
        "cost_spirit_stones": 0,
    },
    {
        "id": "yandao_tianshu_xia",
        "name": "衍道天书·下卷",
        "dao_path": "yan",
        "grade": TechniqueGrade.HONGMENG,
        "sub_grade": TechniqueSubGrade.UNIQUE,
        "min_realm": 32,
        "max_realm": 32,
        "exp_multiplier": 5.0,
        "dao_gain": {"yan": 50},
        "breakthrough_bonus": 0.10,
        "combat_bonus": {"attack_pct": 0.22, "defense_pct": 0.22, "hp_pct": 0.25},
        "special": "鸿蒙之力：适应万法，受到的所有伤害降低15%，炼丹炼器必成",
        "desc": "三大天书之三，记载衍道终极奥义",
        "cost_spirit_stones": 0,
    },

    # ========================= 兼修/旁门系列 =========================

    # --- 剑修 ---
    {
        "id": "wanjian_guizong",
        "name": "万剑归宗诀",
        "dao_path": "misc",
        "grade": TechniqueGrade.LING,
        "sub_grade": TechniqueSubGrade.SHANG,
        "min_realm": 6,
        "max_realm": 21,
        "exp_multiplier": 1.4,
        "dao_gain": {"ni": 3, "heng": 2},
        "breakthrough_bonus": 0.01,
        "combat_bonus": {"attack_pct": 0.15, "crit_rate": 0.05},
        "special": "剑意：普攻有10%概率触发剑气追击，造成50%额外伤害",
        "desc": "以万剑为一，一剑破万法。剑修正统功法",
        "cost_spirit_stones": 8000,
    },
    {
        "id": "dugu_jianjue",
        "name": "独孤剑诀",
        "dao_path": "misc",
        "grade": TechniqueGrade.XIAN,
        "sub_grade": TechniqueSubGrade.ZHONG,
        "min_realm": 22,
        "max_realm": 32,
        "exp_multiplier": 2.0,
        "dao_gain": {"ni": 8, "heng": 4},
        "breakthrough_bonus": 0.03,
        "combat_bonus": {"attack_pct": 0.22, "crit_rate": 0.10, "crit_damage": 0.15},
        "special": "无敌剑意：未被命中的回合攻击额外+10%（可叠加3层）",
        "desc": "一人一剑，独步天下。传说中的仙级剑修绝学",
        "cost_spirit_stones": 2000000,
    },

    # --- 炼体 ---
    {
        "id": "jingang_buhui",
        "name": "金刚不坏体",
        "dao_path": "misc",
        "grade": TechniqueGrade.LING,
        "sub_grade": TechniqueSubGrade.ZHONG,
        "min_realm": 6,
        "max_realm": 25,
        "exp_multiplier": 1.2,
        "dao_gain": {"heng": 3, "yan": 2},
        "breakthrough_bonus": 0.02,
        "combat_bonus": {"defense_pct": 0.20, "hp_pct": 0.15},
        "special": "金刚体：受到致命伤害时有8%概率保留1点生命",
        "desc": "肉身成圣之路，以血肉铸就不灭金身",
        "cost_spirit_stones": 6000,
    },

    # --- 魂修 ---
    {
        "id": "hunpo_tianluo",
        "name": "魂魄天罗术",
        "dao_path": "misc",
        "grade": TechniqueGrade.LING,
        "sub_grade": TechniqueSubGrade.SHANG,
        "min_realm": 10,
        "max_realm": 25,
        "exp_multiplier": 1.5,
        "dao_gain": {"ni": 4, "yan": 3},
        "breakthrough_bonus": 0.01,
        "combat_bonus": {"mp_pct": 0.15, "skill_damage_pct": 0.10},
        "special": "魂攻：技能攻击有8%概率使敌人眩晕1回合",
        "desc": "修炼神魂，以魂力为武器的旁门功法",
        "cost_spirit_stones": 15000,
    },
    {
        "id": "jiuyou_hunyin",
        "name": "九幽魂引经",
        "dao_path": "misc",
        "grade": TechniqueGrade.XIAN,
        "sub_grade": TechniqueSubGrade.XIA,
        "min_realm": 22,
        "max_realm": 32,
        "exp_multiplier": 2.2,
        "dao_gain": {"ni": 10, "yan": 5},
        "breakthrough_bonus": 0.02,
        "combat_bonus": {"mp_pct": 0.20, "skill_damage_pct": 0.18},
        "special": "九幽魂火：技能暴击时附加持续灼烧，3回合内每回合损失3%血量",
        "desc": "九幽之下，万魂臣服。高阶魂修至高秘典",
        "cost_spirit_stones": 1000000,
    },

    # --- 阵道 ---
    {
        "id": "tianji_zhenshu",
        "name": "天机阵术",
        "dao_path": "misc",
        "grade": TechniqueGrade.LING,
        "sub_grade": TechniqueSubGrade.ZHONG,
        "min_realm": 10,
        "max_realm": 25,
        "exp_multiplier": 1.3,
        "dao_gain": {"yan": 5, "heng": 2},
        "breakthrough_bonus": 0.01,
        "combat_bonus": {"defense_pct": 0.10, "dodge_rate": 0.05},
        "special": "阵法加持：防御战中防御额外+15%，秘境探索奖励+10%",
        "desc": "以天地为阵盘，万物为阵眼的奇门阵法",
        "cost_spirit_stones": 12000,
    },

    # --- 器道 ---
    {
        "id": "baiqi_jing",
        "name": "百器经",
        "dao_path": "misc",
        "grade": TechniqueGrade.LING,
        "sub_grade": TechniqueSubGrade.XIA,
        "min_realm": 6,
        "max_realm": 21,
        "exp_multiplier": 1.1,
        "dao_gain": {"yan": 4, "heng": 2},
        "breakthrough_bonus": 0.0,
        "combat_bonus": {"attack_pct": 0.05},
        "special": "器灵亲和：装备法宝属性加成额外+10%，炼器成功率+5%",
        "desc": "器道入门，与万器沟通的基础功法",
        "cost_spirit_stones": 5000,
    },

    # --- 丹道 ---
    {
        "id": "wanhuo_danjing",
        "name": "万火丹经",
        "dao_path": "misc",
        "grade": TechniqueGrade.LING,
        "sub_grade": TechniqueSubGrade.SHANG,
        "min_realm": 6,
        "max_realm": 25,
        "exp_multiplier": 1.3,
        "dao_gain": {"yan": 5, "heng": 3},
        "breakthrough_bonus": 0.01,
        "combat_bonus": {"skill_damage_pct": 0.05},
        "special": "丹火：炼丹成功率+10%，丹药效果持续时间+20%",
        "desc": "以丹入道，火炼万物。丹修正统功法",
        "cost_spirit_stones": 10000,
    },

    # --- 毒修 ---
    {
        "id": "wandu_zhenjing",
        "name": "万毒真经",
        "dao_path": "misc",
        "grade": TechniqueGrade.LING,
        "sub_grade": TechniqueSubGrade.SHANG,
        "min_realm": 10,
        "max_realm": 25,
        "exp_multiplier": 1.4,
        "dao_gain": {"ni": 5, "yan": 3},
        "breakthrough_bonus": 0.0,
        "combat_bonus": {"attack_pct": 0.08},
        "special": "百毒不侵：免疫中毒状态；攻击有12%概率使目标中毒（每回合损失2%血量，持续3回合）",
        "desc": "以毒入道，万毒归一。毒修至高功法",
        "cost_spirit_stones": 18000,
    },

    # --- 音修 ---
    {
        "id": "tianlai_xiange",
        "name": "天籁仙歌",
        "dao_path": "misc",
        "grade": TechniqueGrade.LING,
        "sub_grade": TechniqueSubGrade.ZHONG,
        "min_realm": 6,
        "max_realm": 21,
        "exp_multiplier": 1.3,
        "dao_gain": {"heng": 3, "yan": 4},
        "breakthrough_bonus": 0.01,
        "combat_bonus": {"mp_pct": 0.10},
        "special": "天籁之音：战斗开始时有15%概率使敌人迷惑1回合（跳过行动）",
        "desc": "以音律感悟天道，攻守兼备的音修功法",
        "cost_spirit_stones": 7000,
    },

    # --- 符修 ---
    {
        "id": "lingfu_tianshu",
        "name": "灵符天术",
        "dao_path": "misc",
        "grade": TechniqueGrade.LING,
        "sub_grade": TechniqueSubGrade.ZHONG,
        "min_realm": 6,
        "max_realm": 25,
        "exp_multiplier": 1.2,
        "dao_gain": {"yan": 5, "heng": 2},
        "breakthrough_bonus": 0.01,
        "combat_bonus": {"skill_damage_pct": 0.08, "mp_pct": 0.08},
        "special": "符箓加持：使用消耗品时效果+15%",
        "desc": "以符通灵，一笔一画皆是天道法则",
        "cost_spirit_stones": 8000,
    },

    # --- 兼修通用 ---
    {
        "id": "hunkun_gong",
        "name": "混沌功",
        "dao_path": "misc",
        "grade": TechniqueGrade.FAN,
        "sub_grade": TechniqueSubGrade.ZHONG,
        "min_realm": 1,
        "max_realm": 9,
        "exp_multiplier": 0.9,
        "dao_gain": {"heng": 1, "ni": 1, "yan": 1},
        "breakthrough_bonus": 0.01,
        "combat_bonus": {"attack_pct": 0.03, "defense_pct": 0.03},
        "special": "三道兼修：三道亲和度均衡增长",
        "desc": "不偏不倚，兼修三道的入门功法。成长慢但路子宽",
        "cost_spirit_stones": 0,
    },
    {
        "id": "taixuan_shengong",
        "name": "太玄神功",
        "dao_path": "misc",
        "grade": TechniqueGrade.XIAN,
        "sub_grade": TechniqueSubGrade.SHANG,
        "min_realm": 26,
        "max_realm": 32,
        "exp_multiplier": 2.5,
        "dao_gain": {"heng": 8, "ni": 8, "yan": 8},
        "breakthrough_bonus": 0.04,
        "combat_bonus": {"attack_pct": 0.15, "defense_pct": 0.12, "hp_pct": 0.10},
        "special": "太玄归一：三道亲和度最高者额外触发专属效果",
        "desc": "兼修三道之极致，合体以上方可参悟",
        "cost_spirit_stones": 3000000,
    },

    # --- 邪修 ---
    {
        "id": "jiuyin_xiegong",
        "name": "九阴邪功",
        "dao_path": "misc",
        "grade": TechniqueGrade.FAN,
        "sub_grade": TechniqueSubGrade.JI,
        "min_realm": 2,
        "max_realm": 13,
        "exp_multiplier": 1.5,
        "dao_gain": {"ni": 5},
        "breakthrough_bonus": -0.03,
        "combat_bonus": {"attack_pct": 0.12, "hp_pct": -0.05},
        "special": "嗜血：击杀后恢复20%生命，但每次修炼有3%概率走火入魔",
        "desc": "邪门歪道的速成功法，修炼快但代价沉重",
        "cost_spirit_stones": 300,
    },

    # --- 佛修 ---
    {
        "id": "dabei_xinfa",
        "name": "大悲心法",
        "dao_path": "misc",
        "grade": TechniqueGrade.LING,
        "sub_grade": TechniqueSubGrade.JI,
        "min_realm": 10,
        "max_realm": 29,
        "exp_multiplier": 1.6,
        "dao_gain": {"heng": 6, "yan": 3},
        "breakthrough_bonus": 0.03,
        "combat_bonus": {"hp_pct": 0.12, "defense_pct": 0.10},
        "special": "金刚法身：受到暴击伤害降低20%；每回合恢复1%血量",
        "desc": "佛门至高心法，慈悲为怀，以守代攻",
        "cost_spirit_stones": 25000,
    },
]


# ---------------------------------------------------------------------------
# 丹药体系
# ---------------------------------------------------------------------------
# pill_grade: huang(黄), xuan(玄), di(地), tian(天), xian(仙), shen(神)
# effect_type: cultivation(修炼), breakthrough(突破), combat(战斗), recovery(恢复)

PILL_GRADES = {
    "huang": "黄级",
    "xuan": "玄级",
    "di": "地级",
    "tian": "天级",
    "xian": "仙级",
    "shen": "神级",
}

PILL_GRADE_ORDER: Dict[str, int] = {
    "huang": 0,
    "xuan": 1,
    "di": 2,
    "tian": 3,
    "xian": 4,
    "shen": 5,
}

PILLS: List[Dict[str, Any]] = [
    # ========================= 黄级丹药 =========================
    {
        "id": "juqi_dan",
        "name": "聚气丹",
        "pill_grade": "huang",
        "effect_type": "cultivation",
        "effect": {"exp_multiplier": 1.5, "duration_sessions": 3},
        "min_realm": 1,
        "max_realm": 5,
        "desc": "辅助炼气修炼，提升灵气吸收效率",
    },
    {
        "id": "huiqi_dan",
        "name": "回气丹",
        "pill_grade": "huang",
        "effect_type": "recovery",
        "effect": {"hp_restore_pct": 0.30, "mp_restore_pct": 0.20},
        "min_realm": 1,
        "max_realm": 9,
        "desc": "恢复气血灵力的基础丹药",
    },
    {
        "id": "zhuji_dan",
        "name": "筑基丹",
        "pill_grade": "huang",
        "effect_type": "breakthrough",
        "effect": {"breakthrough_bonus": 0.10},
        "min_realm": 5,
        "max_realm": 6,
        "desc": "筑基专用突破丹，提升成功率10%",
    },

    # ========================= 玄级丹药 =========================
    {
        "id": "ningdan_dan",
        "name": "凝丹丸",
        "pill_grade": "xuan",
        "effect_type": "breakthrough",
        "effect": {"breakthrough_bonus": 0.12},
        "min_realm": 9,
        "max_realm": 10,
        "desc": "辅助金丹凝聚，提升结丹成功率",
    },
    {
        "id": "pozhang_dan",
        "name": "破障丹",
        "pill_grade": "xuan",
        "effect_type": "cultivation",
        "effect": {"exp_multiplier": 1.8, "duration_sessions": 3},
        "min_realm": 6,
        "max_realm": 13,
        "desc": "打破修炼瓶颈，大幅提升修炼速度",
    },
    {
        "id": "huxin_dan",
        "name": "护心丹",
        "pill_grade": "xuan",
        "effect_type": "combat",
        "effect": {"defense_pct": 0.15, "hp_pct": 0.10, "duration_rounds": 10},
        "min_realm": 6,
        "max_realm": 17,
        "desc": "护住心脉，战斗中大幅提升防御",
    },

    # ========================= 地级丹药 =========================
    {
        "id": "yuanying_dan",
        "name": "元婴丹",
        "pill_grade": "di",
        "effect_type": "breakthrough",
        "effect": {"breakthrough_bonus": 0.15},
        "min_realm": 13,
        "max_realm": 14,
        "desc": "凝聚元婴专用，极为珍贵的突破丹药",
    },
    {
        "id": "tiansui_dan",
        "name": "天髓丹",
        "pill_grade": "di",
        "effect_type": "cultivation",
        "effect": {"exp_multiplier": 2.0, "duration_sessions": 5},
        "min_realm": 14,
        "max_realm": 21,
        "desc": "天地精华凝结而成，修炼效率翻倍",
    },

    # ========================= 天级丹药 =========================
    {
        "id": "huashen_dan",
        "name": "化神丹",
        "pill_grade": "tian",
        "effect_type": "breakthrough",
        "effect": {"breakthrough_bonus": 0.18},
        "min_realm": 17,
        "max_realm": 18,
        "desc": "化神必备，一颗难求的天级突破丹",
    },
    {
        "id": "jiutian_lingyun_dan",
        "name": "九天凌云丹",
        "pill_grade": "tian",
        "effect_type": "cultivation",
        "effect": {"exp_multiplier": 2.5, "duration_sessions": 5},
        "min_realm": 18,
        "max_realm": 29,
        "desc": "凌驾九天之上的修炼圣药",
    },
    {
        "id": "baolie_dan",
        "name": "暴烈丹",
        "pill_grade": "tian",
        "effect_type": "combat",
        "effect": {"attack_pct": 0.25, "crit_rate": 0.10, "duration_rounds": 8},
        "min_realm": 18,
        "max_realm": 29,
        "desc": "战斗爆发型丹药，短时间内大幅提升攻击力",
    },

    # ========================= 仙级丹药 =========================
    {
        "id": "dujie_dan",
        "name": "渡劫丹",
        "pill_grade": "xian",
        "effect_type": "breakthrough",
        "effect": {"breakthrough_bonus": 0.20},
        "min_realm": 30,
        "max_realm": 31,
        "desc": "渡劫飞升专用，仙级至宝",
    },
    {
        "id": "taiyi_xianlu",
        "name": "太乙仙露",
        "pill_grade": "xian",
        "effect_type": "recovery",
        "effect": {"hp_restore_pct": 1.0, "mp_restore_pct": 1.0},
        "min_realm": 30,
        "max_realm": 32,
        "desc": "完全恢复气血灵力的仙级灵药",
    },

    # ========================= 神级丹药 =========================
    {
        "id": "zaohua_shenyuan",
        "name": "造化神元丹",
        "pill_grade": "shen",
        "effect_type": "cultivation",
        "effect": {"exp_multiplier": 5.0, "duration_sessions": 3},
        "min_realm": 32,
        "max_realm": 32,
        "desc": "蕴含造化之力的终极修炼丹药，仅真仙可服",
    },
    {
        "id": "hundun_shenlian",
        "name": "混沌神莲",
        "pill_grade": "shen",
        "effect_type": "combat",
        "effect": {"attack_pct": 0.30, "defense_pct": 0.30, "hp_pct": 0.20, "duration_rounds": 15},
        "min_realm": 32,
        "max_realm": 32,
        "desc": "混沌莲花所化，全属性大幅提升",
    },
]


# ---------------------------------------------------------------------------
# 内部索引 —— 模块加载时构建一次，后续查询 O(1)
# ---------------------------------------------------------------------------

_TECHNIQUE_INDEX: Dict[str, Dict[str, Any]] = {t["id"]: t for t in TECHNIQUES}
_PILL_INDEX: Dict[str, Dict[str, Any]] = {p["id"]: p for p in PILLS}


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------

def get_technique(tech_id: str) -> Optional[Dict[str, Any]]:
    """根据功法ID获取功法数据，找不到返回 None"""
    return _TECHNIQUE_INDEX.get(tech_id)


def get_techniques_by_dao(dao_path: str) -> List[Dict[str, Any]]:
    """按道途筛选功法列表（heng / ni / yan / misc）"""
    return [t for t in TECHNIQUES if t["dao_path"] == dao_path]


def get_available_techniques(realm_id: int) -> List[Dict[str, Any]]:
    """获取当前境界可学习的所有功法（min_realm <= realm_id <= max_realm）"""
    return [
        t for t in TECHNIQUES
        if t["min_realm"] <= realm_id <= t["max_realm"]
    ]


def get_pill(pill_id: str) -> Optional[Dict[str, Any]]:
    """根据丹药ID获取丹药数据，找不到返回 None"""
    return _PILL_INDEX.get(pill_id)


def get_available_pills(realm_id: int) -> List[Dict[str, Any]]:
    """获取当前境界可使用的所有丹药"""
    return [
        p for p in PILLS
        if p["min_realm"] <= realm_id <= p["max_realm"]
    ]


def technique_grade_rank(tech: Dict[str, Any]) -> int:
    """
    返回功法的综合品阶排序值，数值越大品阶越高。
    用于排序和比较：grade * 10 + sub_grade。
    """
    g = tech["grade"].value if isinstance(tech["grade"], TechniqueGrade) else tech["grade"]
    sg = tech["sub_grade"].value if isinstance(tech["sub_grade"], TechniqueSubGrade) else tech["sub_grade"]
    return GRADE_ORDER.get(g, 0) * 10 + SUB_GRADE_ORDER.get(sg, 0)


def format_technique_grade(tech: Dict[str, Any]) -> str:
    """返回功法品级的中文描述，如 '灵级·上品'"""
    g = tech["grade"].value if isinstance(tech["grade"], TechniqueGrade) else tech["grade"]
    sg = tech["sub_grade"].value if isinstance(tech["sub_grade"], TechniqueSubGrade) else tech["sub_grade"]
    grade_cn = GRADE_CN.get(g, g)
    sub_cn = SUB_GRADE_CN.get(sg, sg)
    if sub_cn:
        return f"{grade_cn}·{sub_cn}"
    return grade_cn
