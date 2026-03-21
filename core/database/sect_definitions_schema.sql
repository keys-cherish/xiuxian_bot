-- ============================================================
-- 宗门体系 · PostgreSQL
-- 13个宗门（正道5/邪道4/中立4）
-- 含招聘会、每日资源发放、面试条件
-- ============================================================

-- 宗门定义表（系统预设，不可由玩家创建）
CREATE TABLE IF NOT EXISTS sect_definitions (
    sect_id          TEXT PRIMARY KEY,
    name             TEXT NOT NULL,
    faction          TEXT NOT NULL,         -- righteous(正道)/evil(邪道)/neutral(中立)
    dao_affinity     TEXT,                  -- heng/ni/yan/mixed
    description      TEXT,
    motto            TEXT,                  -- 门派口号
    sect_level       INTEGER DEFAULT 1,     -- 宗门等级 1-10
    generosity       REAL DEFAULT 0.5,      -- 大方程度 0-1（影响每日资源）
    oppression       REAL DEFAULT 0.0,      -- 压榨程度 0-1（高则资源多但心境扣）
    max_members      INTEGER DEFAULT 50,    -- 招收上限
    current_members  INTEGER DEFAULT 0,
    min_realm        INTEGER DEFAULT 2,     -- 最低入门境界
    required_element TEXT,                  -- 要求灵根属性（NULL=不限）
    required_tags    JSONB DEFAULT '[]',    -- 蝴蝶效应标签要求
    daily_copper     INTEGER DEFAULT 100,   -- 每日基础灵石发放
    daily_exp        INTEGER DEFAULT 50,    -- 每日基础修为发放
    daily_items      JSONB DEFAULT '[]',    -- 每日物品发放
    cultivation_bonus REAL DEFAULT 0.10,    -- 修炼加成
    stat_bonus       REAL DEFAULT 0.05,     -- 属性加成
    special_skill    TEXT,                  -- 宗门专属可学秘籍ID
    recruitment_open BOOLEAN DEFAULT FALSE, -- 当前是否开放招聘
    next_recruitment TIMESTAMP,             -- 下次招聘时间
    recruitment_interval_hours INTEGER DEFAULT 72, -- 招聘间隔(小时)，小宗门短，大宗门长
    recruitment_slots INTEGER DEFAULT 5,    -- 每次招聘名额
    lore             TEXT,                  -- 宗门故事背景
    interview_scene  TEXT                   -- 面试剧情场景ID
);

-- 宗门成员表
CREATE TABLE IF NOT EXISTS sect_members (
    player_id        BIGINT PRIMARY KEY,
    sect_id          TEXT REFERENCES sect_definitions(sect_id),
    role             TEXT DEFAULT 'outer',  -- outer(外门)/inner(内门)/core(核心)/elder(长老)
    contribution     INTEGER DEFAULT 0,     -- 宗门贡献值
    joined_at        TIMESTAMP DEFAULT NOW(),
    daily_claimed    DATE,                  -- 今日是否已领取资源
    mentality_debt   REAL DEFAULT 0.0       -- 压榨累积的心境负担
);

-- 宗门招聘会日志
CREATE TABLE IF NOT EXISTS sect_recruitment_log (
    id               BIGSERIAL PRIMARY KEY,
    sect_id          TEXT REFERENCES sect_definitions(sect_id),
    opened_at        TIMESTAMP DEFAULT NOW(),
    closed_at        TIMESTAMP,
    slots_offered    INTEGER,
    slots_filled     INTEGER DEFAULT 0,
    requirements     JSONB DEFAULT '{}'     -- 本次招聘的额外条件
);

CREATE INDEX IF NOT EXISTS idx_sect_members_sect ON sect_members(sect_id);
CREATE INDEX IF NOT EXISTS idx_sect_recruit_time ON sect_recruitment_log(opened_at);

-- ============================================================
-- 种子数据：13个宗门
-- ============================================================

BEGIN;

-- ==================== 正道五宗 ====================

INSERT INTO sect_definitions VALUES
('taiqing',  '太清宗', 'righteous', 'heng',
 '天元大陆第一大派，以恒道修行著称，底蕴深厚，弟子众多。',
 '道法自然，恒心不移',
 8, 0.7, 0.1, 80, 0, 5, NULL, '[]',
 200, 100, '[{"id":"herb","qty":2}]',
 0.15, 0.08, 'skill_taiqing_full', FALSE, NULL,
 '太清宗建宗万年，历代掌门皆为恒道大能。宗内讲究循序渐进，根基扎实，虽无逆天之资，却能稳步前行。门下弟子遍布天元大陆各处，是正道的中流砥柱。',
 'interview_taiqing'),

('tianjian', '天剑门', 'righteous', 'mixed',
 '剑修圣地，以剑入道，门下弟子皆为剑修。',
 '一剑破万法',
 7, 0.5, 0.2, 60, 0, 5, NULL, '[]',
 150, 120, '[{"id":"iron_ore","qty":3}]',
 0.12, 0.10, 'skill_tianjian_sword', FALSE, NULL,
 '天剑门立于万剑峰之巅，门内三百六十把古剑日夜嗡鸣。入门弟子需经剑道试炼，以剑心通过者方可拜入门下。天剑门训练极为严苛，但战力冠绝同境。',
 'interview_tianjian'),

('danding',  '丹鼎阁', 'righteous', 'heng',
 '丹道至尊，天下丹师十之七八出自丹鼎阁。',
 '一炉定乾坤',
 7, 0.8, 0.05, 50, 0, 4, NULL, '[]',
 180, 80, '[{"id":"herb","qty":5},{"id":"spirit_stone","qty":1}]',
 0.10, 0.05, 'skill_danding_pill', FALSE, NULL,
 '丹鼎阁不重战力，唯重丹道。门下弟子多为炼丹师，阁中丹方万千，从最基础的回灵丹到逆天续命的九转还魂丹，皆有记载。入门需通过识药和控火测试。',
 'interview_danding'),

('wanfa',    '万法宗', 'righteous', 'mixed',
 '博采众长，兼修百家之法，门风开放。',
 '万法归宗，大道至简',
 6, 0.6, 0.15, 70, 0, 3, NULL, '[]',
 160, 90, '[{"id":"small_exp_pill","qty":1}]',
 0.12, 0.06, 'skill_wanfa_body', FALSE, NULL,
 '万法宗藏经阁中收录了天下大半功法，虽多为残篇，却也让弟子视野开阔。万法宗弟子往往杂而不精，但关键时刻总能出其不意。宗门面试看重悟性而非战力。',
 'interview_wanfa'),

('lingshou', '灵兽谷', 'righteous', 'yan',
 '驭兽世家，谷中豢养万千灵兽，弟子人手一只灵宠。',
 '万兽听令，天地为笼',
 6, 0.65, 0.1, 45, 0, 3, NULL, '[]',
 140, 70, '[{"id":"beast_feed","qty":3}]',
 0.10, 0.05, 'skill_lingshou_bond', FALSE, NULL,
 '灵兽谷隐于万兽山脉深处，谷中灵兽种类繁多，从一阶灵鼠到七阶蛟龙皆有。入门弟子需与一头灵兽缔结初始契约，契约成功率取决于弟子的衍道亲和。',
 'interview_lingshou'),

-- ==================== 邪道四宗 ====================

('nitian',   '逆天殿', 'evil', 'ni',
 '逆道传承，亦正亦邪，以逆天改命为宗旨。',
 '天不容我，我便逆天',
 7, 0.4, 0.35, 40, 0, 6, NULL, '[]',
 120, 150, '[]',
 0.18, 0.12, 'skill_nitian_reverse', FALSE, NULL,
 '逆天殿不问出身，不问过往，只看你是否有逆天之心。殿中修炼残酷至极，十入一出，但活下来的无不是同境无敌的存在。入殿即生死自负，无人庇护。',
 'interview_nitian'),

('xuesha',   '血煞宗', 'evil', 'ni',
 '嗜血修炼，以鲜血为媒淬炼己身。',
 '血海无涯，杀伐即道',
 5, 0.3, 0.5, 35, 0, 5, NULL, '[]',
 80, 130, '[{"id":"blood_pill","qty":1}]',
 0.15, 0.15, 'skill_blood_devour', FALSE, NULL,
 '血煞宗是正道眼中的邪魔外道，宗内修士以血为媒修炼功法，战力极强但折损寿元。血煞宗不设面试，以实力说话——想加入？活着走过血路就行。',
 'interview_xuesha'),

('wangui',   '万鬼门', 'evil', 'yan',
 '鬼修传承，御使鬼魂作战。',
 '生死之间，万鬼听令',
 5, 0.35, 0.4, 30, 0, 5, NULL, '[]',
 90, 110, '[{"id":"ghost_jade","qty":1}]',
 0.12, 0.10, 'skill_ghost_control', FALSE, NULL,
 '万鬼门立于阴山之巅，门中阴气冲天，活人踏入便觉寒意透骨。万鬼门弟子需与第一头冤魂缔结契约，以此为基，逐步驾驭万鬼。面试即与鬼斗。',
 'interview_wangui'),

('tianmo',   '天魔教', 'evil', 'ni',
 '魔道至尊，教义为心随所欲，不受天道束缚。',
 '欲望即力量，我即天道',
 8, 0.3, 0.6, 25, 0, 8, NULL, '[]',
 100, 200, '[]',
 0.20, 0.15, 'skill_demon_body', FALSE, NULL,
 '天魔教是邪道之首，教中强者如云，教主实力深不可测。天魔教弟子修炼天魔功，以心魔为食，越是执念深重之人越适合。入教需经心魔试炼，九死一生。',
 'interview_tianmo'),

-- ==================== 中立四方 ====================

('xingchen', '星辰阁', 'neutral', 'yan',
 '衍道传承，隐世不出，百年开门一次。',
 '星辰大海，万物衍化',
 9, 0.9, 0.0, 15, 0, 10, NULL, '["星力觉醒"]',
 300, 200, '[{"id":"star_dust","qty":2}]',
 0.25, 0.10, 'skill_star_evolution', FALSE, NULL,
 '星辰阁建于星陨山脉之巅，阁中修士夜观星象，以星辰之力修行。星辰阁百年开门一次，每次仅收三至五人，入门条件极为苛刻——须有衍道亲和且感应过星力。',
 'interview_xingchen'),

('luanxing', '乱星海散修联盟', 'neutral', 'mixed',
 '散修聚集之地，无门无派，以实力和信誉立足。',
 '散修亦有道，不拜天不拜地',
 4, 0.5, 0.0, 200, 0, 2, NULL, '[]',
 60, 30, '[]',
 0.05, 0.03, NULL, FALSE, NULL,
 '乱星海散修联盟不是宗门，而是散修们自发形成的互助组织。没有严格的规矩，没有长老训话，进出自由。唯一的规矩是不可对盟友出手。加入门槛极低。',
 'interview_luanxing'),

('manhuang', '蛮荒妖族联盟', 'neutral', 'mixed',
 '妖族与亲妖修士组成的联盟。',
 '万兽之心，天地同寿',
 5, 0.5, 0.2, 40, 0, 4, NULL, '[]',
 100, 80, '[{"id":"beast_core","qty":1}]',
 0.10, 0.08, NULL, FALSE, NULL,
 '蛮荒妖族联盟是万兽山脉深处的妖修势力，接纳化形妖族和亲近妖族的人族修士。联盟中弱肉强食，但对自己人极为护短。入盟需通过妖兽认主试炼。',
 'interview_manhuang')

-- 注意：万宝楼不是可加入的宗门，而是全服公共商会/拍卖行NPC设施
-- 万宝楼的数据在 maps.py 和 items.py 中定义为商店NPC

ON CONFLICT (sect_id) DO NOTHING;

-- 招聘频率设定：小宗门/中立频率高，大宗门/顶级低
-- 单位：小时（现实时间）
UPDATE sect_definitions SET recruitment_interval_hours = 168, recruitment_slots = 3  WHERE sect_id = 'taiqing';   -- 太清宗：7天一次，每次3人
UPDATE sect_definitions SET recruitment_interval_hours = 120, recruitment_slots = 3  WHERE sect_id = 'tianjian';  -- 天剑门：5天一次
UPDATE sect_definitions SET recruitment_interval_hours = 96,  recruitment_slots = 4  WHERE sect_id = 'danding';   -- 丹鼎阁：4天一次
UPDATE sect_definitions SET recruitment_interval_hours = 48,  recruitment_slots = 5  WHERE sect_id = 'wanfa';     -- 万法宗：2天一次（开放门风）
UPDATE sect_definitions SET recruitment_interval_hours = 72,  recruitment_slots = 4  WHERE sect_id = 'lingshou';  -- 灵兽谷：3天一次

UPDATE sect_definitions SET recruitment_interval_hours = 120, recruitment_slots = 2  WHERE sect_id = 'nitian';    -- 逆天殿：5天一次，名额少
UPDATE sect_definitions SET recruitment_interval_hours = 72,  recruitment_slots = 3  WHERE sect_id = 'xuesha';    -- 血煞宗：3天一次
UPDATE sect_definitions SET recruitment_interval_hours = 96,  recruitment_slots = 3  WHERE sect_id = 'wangui';    -- 万鬼门：4天一次
UPDATE sect_definitions SET recruitment_interval_hours = 240, recruitment_slots = 1  WHERE sect_id = 'tianmo';    -- 天魔教：10天一次，每次仅1人

UPDATE sect_definitions SET recruitment_interval_hours = 720, recruitment_slots = 2  WHERE sect_id = 'xingchen';  -- 星辰阁：30天一次（百年开门设定）
UPDATE sect_definitions SET recruitment_interval_hours = 24,  recruitment_slots = 10 WHERE sect_id = 'luanxing';  -- 散修联盟：每天都招（门槛低）
UPDATE sect_definitions SET recruitment_interval_hours = 48,  recruitment_slots = 5  WHERE sect_id = 'manhuang';  -- 妖族联盟：2天一次

COMMIT;
