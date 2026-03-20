-- ============================================================
-- 全局稀缺资源系统 · PostgreSQL
-- 核心思想：法宝/秘籍/稀有丹药是全局有限量资源
--          玩家A买了，全服永久少一件
-- ============================================================

-- 全局限量物品表
CREATE TABLE IF NOT EXISTS global_limited_items (
    item_id          TEXT PRIMARY KEY,
    item_name        TEXT NOT NULL,
    category         TEXT NOT NULL,        -- weapon/armor/skill_book/pill/material/treasure
    rarity           TEXT NOT NULL,        -- common/uncommon/rare/epic/legendary/mythic
    total_supply     INTEGER NOT NULL,     -- 全服总量（创世时确定，不可增加）
    remaining        INTEGER NOT NULL,     -- 剩余数量
    price_type       TEXT DEFAULT 'copper', -- copper/gold/contribution/quest
    base_price       BIGINT DEFAULT 0,
    min_realm        INTEGER DEFAULT 1,    -- 最低境界要求
    source           TEXT DEFAULT 'shop',  -- shop/drop/quest/sect/event
    description      TEXT,
    lore_hint        TEXT,                 -- 获取线索（NPC对话中透露）
    created_at       TIMESTAMP DEFAULT NOW()
);

-- 全局物品交易日志（谁买了什么，不可逆）
CREATE TABLE IF NOT EXISTS global_item_transactions (
    id               BIGSERIAL PRIMARY KEY,
    item_id          TEXT REFERENCES global_limited_items(item_id),
    player_id        BIGINT NOT NULL,
    quantity         INTEGER DEFAULT 1,
    price_paid       BIGINT DEFAULT 0,
    price_type       TEXT DEFAULT 'copper',
    source           TEXT,                 -- 从哪获得的
    acquired_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_global_txn_item ON global_item_transactions(item_id);
CREATE INDEX IF NOT EXISTS idx_global_txn_player ON global_item_transactions(player_id);

-- ============================================================
-- 种子数据：全服限量物品
-- ============================================================

BEGIN;

-- === 突破材料（金丹+需要，线索从NPC口中得知）===
INSERT INTO global_limited_items VALUES
('break_jiedan_pill',    '凝丹露',      'pill',       'rare',      200, 200, 'gold',  500,  9,  'quest',  '金丹突破必需，凝聚丹力之精华',          '陈长老曾提过，丹鼎阁每年只炼制有限数量'),
('break_yuanying_core',  '元婴结晶',    'material',   'epic',      80,  80,  'gold',  2000, 13, 'drop',   '元婴突破必需，蕴含元神之力',            '传闻星陨秘境深处有产出，但数量极少'),
('break_huashen_lotus',  '化神莲台',    'treasure',   'legendary', 30,  30,  'quest', 0,    17, 'quest',  '化神突破必需，需集齐三瓣莲花',          '仙人遗府中或有线索'),
('break_lianxu_void',    '炼虚虚晶',    'material',   'legendary', 15,  15,  'quest', 0,    21, 'quest',  '炼虚突破必需，虚空法则之结晶',          '灵界深处的时空裂隙中偶有出现'),
('break_heti_stone',     '合体道石',    'material',   'mythic',    5,   5,   'quest', 0,    25, 'quest',  '合体突破必需，蕴含天地大道之力',        '传说只有古战场秘境最深处才有'),

-- === 传承秘籍（全服限量，学了就没了）===
('skill_taiqing_full',   '太清养气诀·全篇','skill_book','epic',     50,  50,  'contribution', 500,  6,  'sect',  '太清宗镇派功法完整版',                  '太清宗内门弟子方可借阅'),
('skill_tianjian_sword', '天剑三十六式',    'skill_book','epic',     40,  40,  'contribution', 600,  6,  'sect',  '天剑门不传之秘',                        '天剑门试剑大会前三名可获赐'),
('skill_danding_pill',   '丹鼎九转术',     'skill_book','epic',     35,  35,  'contribution', 700,  6,  'sect',  '丹鼎阁顶级丹方',                        '丹鼎阁炼丹大赛冠军可得'),
('skill_wanfa_body',     '万法归宗诀',     'skill_book','epic',     45,  45,  'contribution', 500,  6,  'sect',  '万法宗兼修百家之法',                     '万法宗藏经阁中有记载'),
('skill_lingshou_bond',  '灵兽契约术',     'skill_book','epic',     30,  30,  'contribution', 600,  6,  'sect',  '灵兽谷驭兽核心法门',                     '灵兽谷长老亲传'),
('skill_nitian_reverse', '逆天改命诀',     'skill_book','legendary',20,  20,  'quest',        0,    10, 'quest', '逆天殿至高秘法，以命搏命',               '逆天殿深处的石碑上刻有残篇'),
('skill_blood_devour',   '噬血大法',       'skill_book','legendary',15,  15,  'drop',         0,    10, 'drop',  '血煞宗禁术，以血为媒',                   '击败血煞宗高手有几率掉落'),
('skill_ghost_control',  '万鬼朝宗',       'skill_book','legendary',12,  12,  'quest',        0,    10, 'quest', '万鬼门至高鬼修法门',                     '万鬼门鬼王殿中封印'),
('skill_demon_body',     '天魔不灭体',     'skill_book','legendary',10,  10,  'quest',        0,    14, 'quest', '天魔教镇教之宝',                         '天魔教最深处，击败教主影分身可得'),
('skill_star_evolution',  '星辰衍化经',     'skill_book','mythic',   8,   8,   'quest',        0,    18, 'quest', '星辰阁不世出之功法',                     '星辰阁百年开门一次，缘者可得'),

-- === 稀有法宝（全服限量）===
('weapon_qingfeng',      '青锋剑',         'weapon',    'rare',      100, 100, 'gold',  300,   6, 'shop',  '天剑门弃徒遗留的灵剑',                   '南市坊市偶尔有售'),
('weapon_blood_blade',   '噬血刀',         'weapon',    'epic',      30,  30,  'drop',  0,     10,'drop',  '血煞宗邪器，饮血越多越强',               '击败血煞宗弟子有几率掉落'),
('weapon_star_hammer',   '陨星锤',         'weapon',    'epic',      25,  25,  'quest', 0,     10,'quest', '天外陨铁锻造，重达千斤',                 '星陨秘境中央的陨石坑中可能找到'),
('weapon_void_flute',    '虚空笛',         'weapon',    'legendary', 8,   8,   'quest', 0,     18,'quest', '仙人遗物，可撕裂空间',                   '仙人遗府最深处的宝库中'),
('armor_ice_silk',       '冰蚕丝衣',       'armor',     'rare',      60,  60,  'gold',  400,   6, 'shop',  '冰蚕吐丝编织，可御寒入骨',               '灵兽谷有库存出售'),
('armor_dragon_scale',   '蛟龙鳞甲',       'armor',     'epic',      20,  20,  'drop',  0,     14,'drop',  '以真龙鳞片锻造，刀枪不入',               '击败天雷蛟有几率掉落'),
('armor_phoenix_robe',   '凤羽仙衣',       'armor',     'legendary', 5,   5,   'quest', 0,     22,'quest', '传说中的仙人衣袍',                       '古战场秘境最深处的宝箱'),

-- === 稀有丹药（限量消耗品）===
('pill_jiuzhuan',        '九转还魂丹',     'pill',      'legendary', 20,  20,  'quest', 0,     14,'quest', '可逆天续命，死而复生一次',               '丹鼎阁镇阁之宝，非大功不赐'),
('pill_breakthrough_sup','破障金丹',       'pill',      'epic',      100, 100, 'gold',  1000,  10,'shop',  '金丹期以上突破成功率+30%',               '万宝楼限量拍卖'),
('pill_wash_marrow',     '洗髓丹',         'pill',      'rare',      150, 150, 'gold',  200,   5, 'shop',  '洗涤经脉杂质，永久提升修炼效率5%',        '丹鼎阁常备药品，但数量有限'),
('pill_spirit_restore',  '凝神丹',         'pill',      'uncommon',  500, 500, 'copper',50,    3, 'shop',  '快速恢复灵力',                           '各大坊市均有售卖')
ON CONFLICT (item_id) DO NOTHING;

COMMIT;
