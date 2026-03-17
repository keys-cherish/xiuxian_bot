# 🎮 TG 修仙文字游戏 · 全技术设计文档

---

## 第一章：技术架构

### 1.1 整体系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Telegram Bot API                          │
│                   (webhook / polling)                        │
└──────────────┬──────────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────────┐
│                   Bot Gateway Layer                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────┐  │
│  │消息路由器 │ │指令解析器│ │会话管理器│ │Inline Keyboard│  │
│  │Router    │ │Parser    │ │Session   │ │  Builder      │  │
│  └──────────┘ └──────────┘ └──────────┘ └───────────────┘  │
└──────────────┬──────────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────────┐
│                   Game Logic Layer                           │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌──────────┐ │
│  │修炼系统│ │战斗系统│ │事件系统│ │交易系统│ │ NPC/AI   │ │
│  │Cultiv. │ │Combat  │ │Event   │ │Trade   │ │ Dialog   │ │
│  └────────┘ └────────┘ └────────┘ └────────┘ └──────────┘ │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌──────────┐ │
│  │探索系统│ │宗门系统│ │排行系统│ │成就系统│ │ 剧情引擎 │ │
│  │Explore │ │Sect    │ │Rank    │ │Achieve │ │ Story    │ │
│  └────────┘ └────────┘ └────────┘ └────────┘ └──────────┘ │
└──────────────┬──────────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────────┐
│                   Data Layer                                 │
│  ┌──────────────┐ ┌──────────┐ ┌─────────────────────────┐ │
│  │  PostgreSQL   │ │  Redis   │ │  AI Service (LLM API)   │ │
│  │  持久化存储    │ │ 缓存/CD  │ │  动态文本生成            │ │
│  └──────────────┘ └──────────┘ └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 技术选型

| 组件         | 推荐方案                  | 备选方案     | 理由                           |
| ------------ | ------------------------- | ------------ | ------------------------------ |
| **语言**     | Python 3.11+              | Node.js / Go | 生态最好，AI 库最多            |
| **TG 框架**  | python-telegram-bot v20+  | aiogram 3.x  | 异步支持好，文档全             |
| **数据库**   | PostgreSQL 15+            | MySQL 8      | JSONB 支持，适合存复杂游戏数据 |
| **缓存**     | Redis 7+                  | —            | CD 冷却、会话状态、排行榜      |
| **ORM**      | SQLAlchemy 2.0 + asyncpg  | Tortoise ORM | 异步 + 类型安全                |
| **AI 文本**  | Claude API / DeepSeek     | GPT-4o       | 用于动态剧情、NPC 对话         |
| **定时任务** | APScheduler / Celery Beat | —            | 离线挂机、定时事件             |
| **部署**     | Docker + Docker Compose   | —            | 一键部署                       |

### 1.3 数据库核心表设计

```sql
-- ==================== 玩家核心表 ====================

CREATE TABLE players (
    id              BIGSERIAL PRIMARY KEY,
    tg_user_id      BIGINT UNIQUE NOT NULL,         -- Telegram 用户ID
    tg_username     VARCHAR(64),
    name            VARCHAR(32) NOT NULL,            -- 角色名
    
    -- 境界系统
    realm           SMALLINT DEFAULT 1,              -- 境界ID (1=炼气一层)
    realm_exp       BIGINT DEFAULT 0,                -- 当前境界修为值
    realm_exp_max   BIGINT DEFAULT 1000,             -- 突破所需修为
    
    -- 三道亲和
    dao_heng        SMALLINT DEFAULT 0,              -- 恒道值 0-1000
    dao_ni          SMALLINT DEFAULT 0,              -- 逆道值
    dao_yan         SMALLINT DEFAULT 0,              -- 衍道值
    
    -- 基础属性
    hp              INT DEFAULT 100,
    hp_max          INT DEFAULT 100,
    mp              INT DEFAULT 50,
    mp_max          INT DEFAULT 50,
    attack          INT DEFAULT 10,
    defense         INT DEFAULT 5,
    spirit          INT DEFAULT 10,                  -- 神识
    comprehension   INT DEFAULT 5,                   -- 悟性
    luck            INT DEFAULT 5,                   -- 气运
    
    -- 心境
    mentality       INT DEFAULT 100,                 -- 心境值 0-100
    
    -- 经济
    spirit_stones   BIGINT DEFAULT 0,                -- 灵石
    
    -- 位置
    current_map     VARCHAR(64) DEFAULT 'canglan_city',
    current_area    VARCHAR(64) DEFAULT 'east_gate',
    
    -- 宗门
    sect_id         INT REFERENCES sects(id),
    sect_role       VARCHAR(16),                     -- 杂役/外门/内门/核心/长老/掌门
    
    -- 状态
    status          VARCHAR(16) DEFAULT 'idle',      -- idle/cultivating/exploring/fighting/in_event
    status_end_at   TIMESTAMP,                       -- 状态结束时间
    
    -- 离线挂机
    last_active     TIMESTAMP DEFAULT NOW(),
    offline_action  VARCHAR(16),                     -- 离线时做什么
    
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

-- ==================== 境界定义表 ====================

CREATE TABLE realms (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(32) NOT NULL,            -- 如 "炼气一层"
    stage           VARCHAR(16),                     -- 大境界: lianqi/zhuji/jiedan...
    sub_level       SMALLINT,                        -- 小层次: 1-15(炼气) 1-4(其他)
    exp_required    BIGINT,                          -- 突破所需修为
    breakthrough_rate SMALLINT DEFAULT 80,           -- 基础突破率%
    hp_bonus        INT DEFAULT 0,
    mp_bonus        INT DEFAULT 0,
    attack_bonus    INT DEFAULT 0,
    defense_bonus   INT DEFAULT 0,
    min_map         VARCHAR(64),                     -- 解锁的最低地图
    tribulation     BOOLEAN DEFAULT FALSE,           -- 是否有天劫
    description     TEXT                             -- 境界描述文案
);

-- ==================== 背包系统 ====================

CREATE TABLE player_items (
    id              BIGSERIAL PRIMARY KEY,
    player_id       BIGINT REFERENCES players(id),
    item_id         INT REFERENCES items(id),
    quantity        INT DEFAULT 1,
    is_equipped     BOOLEAN DEFAULT FALSE,
    durability      INT,
    enhanced_level  SMALLINT DEFAULT 0,
    bound           BOOLEAN DEFAULT FALSE,           -- 是否绑定
    UNIQUE(player_id, item_id, is_equipped)
);

-- ==================== 功法系统 ====================

CREATE TABLE player_skills (
    id              BIGSERIAL PRIMARY KEY,
    player_id       BIGINT REFERENCES players(id),
    skill_id        INT REFERENCES skills(id),
    level           SMALLINT DEFAULT 1,              -- 功法修炼层数
    proficiency     INT DEFAULT 0,                   -- 熟练度
    is_active       BOOLEAN DEFAULT TRUE             -- 是否装备
);

-- ==================== 事件日志 ====================

CREATE TABLE event_logs (
    id              BIGSERIAL PRIMARY KEY,
    player_id       BIGINT REFERENCES players(id),
    event_type      VARCHAR(32),                     -- explore/combat/story/random
    event_id        VARCHAR(64),
    result          JSONB,                           -- 事件结果
    narrative       TEXT,                            -- AI 生成的叙事文本
    created_at      TIMESTAMP DEFAULT NOW()
);

-- ==================== 世界状态 ====================

CREATE TABLE world_state (
    id              SERIAL PRIMARY KEY,
    key             VARCHAR(64) UNIQUE,
    value           JSONB,
    updated_at      TIMESTAMP DEFAULT NOW()
);
-- 例: key='current_season' value='{"season":"秋","effect":"金属性功法+10%"}'
-- 例: key='world_event' value='{"type":"妖兽潮","map":"canglan","remaining_hp":1000000}'
```

### 1.4 Redis 缓存设计

```python
# Redis Key 设计

# 玩家会话状态（TTL: 30分钟）
"session:{tg_user_id}" -> {
    "state": "exploring",           # 当前状态机位置
    "context": {...},               # 当前上下文
    "last_msg_id": 12345,          # 上一条消息ID（用于编辑）
    "conversation_history": [...]   # AI 对话历史（最近10条）
}

# 指令冷却（TTL: 动态）
"cd:{tg_user_id}:{action}" -> timestamp
# 例: "cd:123456:cultivate" -> "2024-01-01 12:00:00"  (修炼CD 10分钟)
# 例: "cd:123456:explore"   -> "2024-01-01 12:05:00"  (探索CD 5分钟)

# 排行榜（Sorted Set）
"rank:realm"     -> {player_id: realm_score, ...}
"rank:combat"    -> {player_id: combat_power, ...}
"rank:wealth"    -> {player_id: spirit_stones, ...}

# 世界BOSS血量
"world_boss:hp"  -> 1000000

# 在线玩家集合
"online_players" -> Set{tg_user_id, ...}
```

### 1.5 项目目录结构

```
krkr2-xianxia-bot/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
│
├── bot/
│   ├── __init__.py
│   ├── main.py                     # 入口
│   ├── config.py                   # 配置
│   │
│   ├── handlers/                   # TG 消息处理器
│   │   ├── __init__.py
│   │   ├── start.py               # /start 新手引导
│   │   ├── cultivate.py           # 修炼相关
│   │   ├── explore.py             # 探索相关
│   │   ├── combat.py              # 战斗相关
│   │   ├── inventory.py           # 背包
│   │   ├── skill.py               # 功法
│   │   ├── sect.py                # 宗门
│   │   ├── trade.py               # 交易
│   │   ├── social.py              # 社交（切磋、组队）
│   │   └── admin.py               # 管理员命令
│   │
│   ├── game/                       # 核心游戏逻辑
│   │   ├── __init__.py
│   │   ├── cultivation.py         # 修炼 & 突破
│   │   ├── combat_engine.py       # 战斗引擎
│   │   ├── event_engine.py        # 事件引擎
│   │   ├── story_engine.py        # 剧情引擎
│   │   ├── exploration.py         # 探索系统
│   │   ├── breakthrough.py        # 突破系统
│   │   ├── tribulation.py         # 天劫系统
│   │   ├── alchemy.py             # 炼丹
│   │   ├── crafting.py            # 炼器
│   │   ├── auction.py             # 拍卖行
│   │   └── world_events.py        # 世界事件
│   │
│   ├── ai/                         # AI 文本生成
│   │   ├── __init__.py
│   │   ├── narrator.py            # 叙事生成器
│   │   ├── npc_dialogue.py        # NPC 对话
│   │   ├── event_writer.py        # 事件文案
│   │   ├── prompts/               # Prompt 模板
│   │   │   ├── narrator.txt
│   │   │   ├── npc_base.txt
│   │   │   ├── combat_narration.txt
│   │   │   └── event_templates.txt
│   │   └── cache.py               # AI 响应缓存
│   │
│   ├── models/                     # 数据模型
│   │   ├── __init__.py
│   │   ├── player.py
│   │   ├── item.py
│   │   ├── skill.py
│   │   ├── realm.py
│   │   ├── sect.py
│   │   └── event.py
│   │
│   ├── data/                       # 静态游戏数据
│   │   ├── realms.json            # 境界数据
│   │   ├── items.json             # 物品数据
│   │   ├── skills.json            # 功法数据
│   │   ├── maps.json              # 地图数据
│   │   ├── npcs.json              # NPC 数据
│   │   ├── events/                # 事件脚本
│   │   │   ├── random_events.json
│   │   │   ├── story_events.json
│   │   │   └── world_events.json
│   │   └── lore/                  # 世界观文本
│   │       └── worldbuilding.md   # ← 你的大纲放这里
│   │
│   ├── ui/                         # TG UI 构建
│   │   ├── __init__.py
│   │   ├── keyboards.py           # InlineKeyboard 工厂
│   │   ├── templates.py           # 消息模板
│   │   ├── formatters.py          # 数据格式化
│   │   └── emoji_map.py           # 表情映射
│   │
│   └── utils/
│       ├── __init__.py
│       ├── cooldown.py            # CD 管理
│       ├── random_utils.py        # 加权随机
│       ├── scheduler.py           # 定时任务
│       └── logger.py
│
├── migrations/                     # 数据库迁移
│   └── ...
│
├── tests/
│   └── ...
│
└── scripts/
    ├── init_db.py                 # 初始化数据库
    ├── import_data.py             # 导入游戏数据
    └── benchmark.py               # 压测
```

---

## 第二章：玩家交互界面设计

### 2.1 主界面（Inline Keyboard）

```
📍 苍澜城·东门
━━━━━━━━━━━━━━━━━━━━━━
🧘 沈无极 | 炼气三层
❤️ HP: 85/100 | 💙 MP: 40/50
⚔️ 攻:15 🛡️ 防:8 | 👁️ 神识:12
━━━━━━━━━━━━━━━━━━━━━━
📊 修为: ████████░░ 78%
🔮 恒道:35 | ⚡逆道:12 | 🌟衍道:8
💎 灵石: 2,450
━━━━━━━━━━━━━━━━━━━━━━

[🧘 修炼] [⚔️ 历练] [🗺️ 探索]
[📦 背包] [📜 功法] [👤 状态]
[🏛️ 宗门] [💬 NPC] [📋 任务]
[🏪 商铺] [⚔️ 切磋] [🏆 排行]
```

### 2.2 消息编辑而非刷屏

```python
# 核心原则：永远编辑同一条消息，不要刷屏

class UIManager:
    """管理每个玩家的 UI 消息"""
    
    async def send_or_edit(self, context, user_id: int, text: str, 
                           keyboard: InlineKeyboardMarkup):
        """如果有旧消息就编辑，没有就新发"""
        session = await self.get_session(user_id)
        
        if session.get("last_msg_id"):
            try:
                await context.bot.edit_message_text(
                    chat_id=user_id,
                    message_id=session["last_msg_id"],
                    text=text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
                return
            except BadRequest:
                pass  # 消息太旧无法编辑，发新的
        
        msg = await context.bot.send_message(
            chat_id=user_id,
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        session["last_msg_id"] = msg.message_id
        await self.save_session(user_id, session)
```

### 2.3 交互流设计（关键）

```
玩家体验流 ≠ 指令响应，而是「沉浸式叙事流」

错误示范：
  玩家点"修炼" → 机器人回复 "修炼成功，获得100修为"  ❌ 死的

正确示范：
  玩家点"修炼" →
  
  ════════════════════════════
  🧘 你盘膝坐于落霞谷后山的静室之中。
  
  灵气如细流般从四方汇聚，沿经脉缓缓运行。
  太清养气诀第三层的口诀在脑海中回荡……
  
  忽然，你感到丹田处微微发热——
  那颗灰暗的珠子再次泛起微弱的光芒。
  
  📊 修炼结果：
  ✅ 修为 +127（鸿蒙珠加成 ×1.3）
  ✅ 恒道亲和 +2
  ✅ 太清养气诀熟练度 +15
  
  ⏰ 下次修炼冷却：9分42秒
  ════════════════════════════
  
  [🧘 继续修炼(CD中)] [🗺️ 去探索] [📊 查看突破进度]
```

---

## 第三章：核心游戏循环

### 3.1 玩家每日推动路径

```
                    ┌──────────────┐
            ┌──────▶│   修 炼       │──── 积累修为 ──┐
            │       │ (主要成长)    │                │
            │       └──────────────┘                │
            │                                       │
   ┌────────┴───────┐                    ┌──────────▼────────┐
   │   登录 / 签到   │                    │    突破 / 天劫     │
   │  离线收益结算   │                    │   (里程碑事件)     │
   └────────┬───────┘                    └──────────┬────────┘
            │                                       │
            │       ┌──────────────┐                │
            ├──────▶│   探 索       │◀───────────────┘
            │       │ (随机事件)    │──── 获得资源 ──┐
            │       └──────────────┘                │
            │                                       │
            │       ┌──────────────┐    ┌───────────▼───────┐
            ├──────▶│   历 练       │    │   炼丹 / 炼器      │
            │       │ (战斗刷怪)    │    │   (资源消耗转化)    │
            │       └──────┬───────┘    └───────────┬───────┘
            │              │                        │
            │              ▼                        ▼
            │       ┌──────────────┐    ┌───────────────────┐
            ├──────▶│  任务 / 剧情  │    │   交易 / 拍卖      │
            │       │  (主线推进)   │    │   (社交经济)       │
            │       └──────────────┘    └───────────────────┘
            │
            │       ┌──────────────┐
            └──────▶│  社交 / 宗门  │
                    │ (PVP/合作)    │
                    └──────────────┘
```

### 3.2 修炼系统（核心循环）

```python
class CultivationSystem:
    
    async def cultivate(self, player_id: int) -> CultivationResult:
        player = await self.get_player(player_id)
        
        # 1. 检查冷却
        cd = await self.check_cooldown(player_id, "cultivate")
        if cd > 0:
            return CultivationResult(success=False, cd_remaining=cd)
        
        # 2. 计算基础修为获取
        base_exp = self._calc_base_exp(player)
        
        # 3. 功法加成
        skill_multiplier = self._get_skill_multiplier(player)
        
        # 4. 地图灵气加成
        map_multiplier = self._get_map_spirit_density(player.current_map)
        
        # 5. 鸿蒙珠加成（金手指，随境界解锁）
        pearl_multiplier = self._get_pearl_bonus(player)
        
        # 6. 随机波动 (0.8 ~ 1.5)
        random_factor = random.uniform(0.8, 1.5)
        
        # 7. 顿悟判定（低概率高回报）
        enlightenment = False
        if random.random() < player.comprehension * 0.001:  # 悟性影响
            random_factor *= 5.0
            enlightenment = True
        
        # 8. 走火入魔判定（低概率负面）
        qi_deviation = False
        if random.random() < 0.005 * (1 - player.mentality / 100):
            qi_deviation = True
        
        # 最终计算
        total_exp = int(base_exp * skill_multiplier * map_multiplier 
                       * pearl_multiplier * random_factor)
        
        # 9. 三道亲和增长（根据修炼的功法）
        dao_gains = self._calc_dao_gains(player)
        
        # 10. 更新数据
        await self._apply_cultivation(player, total_exp, dao_gains, 
                                       enlightenment, qi_deviation)
        
        # 11. 设置冷却
        cd_seconds = self._get_cooldown(player.realm)  # 境界越高CD越长
        await self.set_cooldown(player_id, "cultivate", cd_seconds)
        
        # 12. 检查是否可以突破
        can_breakthrough = player.realm_exp + total_exp >= player.realm_exp_max
        
        return CultivationResult(
            success=True,
            exp_gained=total_exp,
            dao_gains=dao_gains,
            enlightenment=enlightenment,
            qi_deviation=qi_deviation,
            can_breakthrough=can_breakthrough,
            cooldown=cd_seconds
        )
    
    def _calc_base_exp(self, player) -> int:
        """基础修为 = 境界基数 × (1 + 悟性/100)"""
        realm_data = REALMS[player.realm]
        return int(realm_data["base_exp_per_session"] * (1 + player.comprehension / 100))
    
    def _get_cooldown(self, realm: int) -> int:
        """
        修炼CD设计（关键平衡点）：
        炼气: 5分钟   → 一天可修炼 ~288次，快速上手
        筑基: 10分钟  → ~144次
        结丹: 20分钟  → ~72次
        元婴: 30分钟  → ~48次
        化神: 1小时   → ~24次
        
        越高级越需要"等待"，但每次收益也越大
        这迫使玩家去做其他事情（探索、战斗）而不是纯挂机
        """
        CD_TABLE = {
            "lianqi": 300,      # 5分钟
            "zhuji": 600,       # 10分钟
            "jiedan": 1200,     # 20分钟
            "yuanying": 1800,   # 30分钟
            "huashen": 3600,    # 1小时
        }
        stage = REALMS[realm]["stage"]
        return CD_TABLE.get(stage, 3600)
```

### 3.3 突破系统（关键爽点）

```python
class BreakthroughSystem:
    
    async def attempt_breakthrough(self, player_id: int) -> BreakthroughResult:
        player = await self.get_player(player_id)
        realm_data = REALMS[player.realm]
        next_realm = REALMS[player.realm + 1]
        
        # ====== 突破三要素 ======
        
        # 1. 悟 — 功法是否满足
        skill_ready = self._check_skill_requirement(player, next_realm)
        
        # 2. 财 — 资源是否满足
        resource_ready = self._check_resource_requirement(player, next_realm)
        
        # 3. 心 — 心境判定
        mentality_bonus = player.mentality / 100  # 0~1
        
        if not skill_ready:
            return BreakthroughResult(
                success=False, 
                reason="功法修为不足",
                narrative="你试图冲击瓶颈，但体内灵力运转不畅，功法尚未圆满……"
            )
        
        if not resource_ready:
            return BreakthroughResult(
                success=False,
                reason="资源不足",
                narrative="灵力在瓶颈处猛烈冲击，但缺少丹药辅助，功亏一篑。"
            )
        
        # ====== 计算成功率 ======
        base_rate = next_realm["breakthrough_rate"] / 100  # 如 0.8
        
        # 悟性加成
        comp_bonus = player.comprehension * 0.005  # 悟性50 = +25%
        
        # 心境加成
        ment_bonus = mentality_bonus * 0.2  # 心境100 = +20%
        
        # 三道亲和加成（如果下一境界偏向某道）
        dao_bonus = self._calc_dao_bonus(player, next_realm)
        
        # 丹药加成
        pill_bonus = self._get_pill_bonus(player)
        
        final_rate = min(0.95, base_rate + comp_bonus + ment_bonus + dao_bonus + pill_bonus)
        
        # ====== 掷骰 ======
        roll = random.random()
        success = roll < final_rate
        
        if success:
            # 突破成功！
            await self._apply_breakthrough(player, next_realm)
            
            # 大境界突破有特殊效果
            if self._is_major_breakthrough(player.realm, player.realm + 1):
                await self._trigger_major_breakthrough_event(player)
            
            # 生成叙事
            narrative = await self.ai_narrator.generate_breakthrough(
                player=player,
                new_realm=next_realm,
                context="success"
            )
            
            # 全服广播（元婴以上）
            if next_realm["stage"] in ("yuanying", "huashen", "lianxu", "heti", "dacheng"):
                await self._broadcast(
                    f"⚡ 天地异象！{player.name} 突破至【{next_realm['name']}】！"
                )
            
            return BreakthroughResult(success=True, narrative=narrative, new_realm=next_realm)
        else:
            # 突破失败
            penalty = self._calc_failure_penalty(player, next_realm)
            await self._apply_failure(player, penalty)
            
            narrative = await self.ai_narrator.generate_breakthrough(
                player=player,
                new_realm=next_realm,
                context="failure",
                penalty=penalty
            )
            
            return BreakthroughResult(
                success=False, 
                narrative=narrative,
                penalty=penalty
            )
```

### 3.4 突破展示效果（玩家看到的）

```
成功：

═══════════════════════════════
⚡ 天 地 异 象 ⚡
═══════════════════════════════

你盘坐于洞府之中，吞下那枚珍贵的破障丹。

滚烫的药力如岩浆般涌入经脉，与体内灵力
交汇、碰撞、融合——

丹田之中，金丹猛然震颤！

"轰——！"

一声闷响在你体内炸开。金丹表面出现细密
的裂纹，如蛛网般蔓延……

你咬紧牙关，全力催动太清养气诀！

"啪！"

金丹碎裂！一道婴儿般的虚影从碎裂的金丹
中缓缓浮出——

三色元婴，睁开了眼睛。

🎉 恭喜！突破成功！
━━━━━━━━━━━━━━━━━━━━━━
📈 炼气三层 → 【元婴初期】
❤️ HP: 100 → 2500
💙 MP: 50 → 800
⚔️ 攻击: 15 → 380
🛡️ 防御: 8 → 200
👁️ 神识: 12 → 150
⏳ 寿元: 500年 → 1000年
🗺️ 解锁地图：【星陨海】
📜 解锁功法：【混元大道经】
═══════════════════════════════

[📊 查看新属性] [🗺️ 前往新地图] [🎉 分享成就]


失败：

═══════════════════════════════
💔 突 破 失 败
═══════════════════════════════

你强行冲击瓶颈，灵力在经脉中暴走——

一阵剧痛从丹田传来，金丹表面的裂纹
迅速愈合，机缘稍纵即逝。

你口中溢出一丝鲜血，面色苍白。

这次失败不仅消耗了丹药，还让你的
根基受到了轻微损伤……

📉 突破失败：
❌ 修为 -15%（根基受损）
❌ 心境 -10（信心动摇）
❌ 消耗：破障丹 ×1
💡 提示：提升心境和悟性可增加成功率
━━━━━━━━━━━━━━━━━━━━━━
当前成功率预估：62%
建议：找到顿悟机缘或提升功法修为后再试
═══════════════════════════════

[🧘 恢复修炼] [🗺️ 寻找机缘] [💊 购买丹药]
```

---

## 第四章：事件系统 —— 让世界「活」起来的核心

### 4.1 事件分层架构

```
事件系统
├── 微事件（每次操作都可能触发）
│   ├── 修炼微事件（修炼时）
│   ├── 探索微事件（探索时）
│   └── 行走微事件（切换地图时）
│
├── 小事件（每天遇到 5-15 个）
│   ├── 随机遭遇
│   ├── NPC 互动
│   └── 环境事件
│
├── 中事件（每周 2-3 个）
│   ├── 支线任务
│   ├── 秘境开启
│   └── 宗门事务
│
├── 大事件（每月 1-2 个）
│   ├── 剧情主线推进
│   ├── 世界事件（全服）
│   └── 大型副本
│
└── 史诗事件（每个境界大阶段 1 个）
    ├── 天劫
    ├── 飞升
    └── 命运抉择
```

### 4.2 微事件设计（渗透到每个操作）

```python
# 微事件：玩家感受不到"事件"，但感受到"世界在呼吸"

CULTIVATION_MICRO_EVENTS = [
    {
        "id": "bird_song",
        "weight": 30,
        "text": "修炼间隙，一只灵雀落在窗棂上，婉转鸣叫了几声便飞走了。你心中微微宁静。",
        "effect": {"mentality": +1},
        "condition": lambda p: p.current_map == "luoxia_valley"
    },
    {
        "id": "spirit_fluctuation",
        "weight": 20,
        "text": "你隐约感到远处传来一阵灵力波动，似乎有人在激烈交手……与你无关，但那股气息让你对「力量」有了更深的渴望。",
        "effect": {"mentality": +2},
        "condition": lambda p: True
    },
    {
        "id": "pearl_glow",
        "weight": 10,
        "text": "鸿蒙珠忽然微微发亮，你能感觉到它似乎在与远方的某种存在产生共鸣……但只是一瞬间。",
        "effect": {"dao_heng": +1},
        "condition": lambda p: p.realm >= 3  # 结丹以上
    },
    {
        "id": "fellow_disciple",
        "weight": 25,
        "text": "隔壁静室传来同门师兄突破的欢呼声。你默默为他高兴，同时暗暗给自己加了把劲。",
        "effect": {"realm_exp": +10},
        "condition": lambda p: p.sect_id is not None
    },
    {
        "id": "rain_spirit",
        "weight": 15,
        "text": "窗外下起了灵雨——这是百年一遇的天象。雨水中蕴含丝丝灵气，你连忙全力运转功法吸收。",
        "effect": {"realm_exp_multiplier": 2.0},  # 本次修炼双倍
        "condition": lambda p: random.random() < 0.03  # 3%概率
    },
    # ... 50+ 微事件
]

EXPLORATION_MICRO_EVENTS = [
    {
        "id": "footprints",
        "weight": 30,
        "text": "你在小路上发现了一串奇怪的脚印，不像人类留下的……脚印延伸到密林深处，你要追踪吗？",
        "choices": [
            {"text": "追踪", "result": "random_encounter"},  # 触发随机遭遇
            {"text": "忽略", "result": None}
        ]
    },
    {
        "id": "herb_discovery",
        "weight": 25,
        "text": "路边的石缝中，一株散发着淡淡灵光的草药引起了你的注意。",
        "effect": {"item": "random_herb"},
        "condition": lambda p: True
    },
    # ... 80+ 微事件
]
```

### 4.3 小事件设计（探索系统核心）

```python
# 探索系统：玩家点击"探索"后进入事件链

class ExplorationEngine:
    
    async def explore(self, player_id: int) -> ExploreResult:
        player = await self.get_player(player_id)
        map_data = MAPS[player.current_map]
        
        # 1. 根据地图权重池抽取事件类型
        event_type = self._weighted_choice(map_data["event_pool"])
        
        # 2. 根据类型生成事件
        if event_type == "combat":
            return await self._generate_combat_encounter(player, map_data)
        elif event_type == "treasure":
            return await self._generate_treasure_event(player, map_data)
        elif event_type == "npc":
            return await self._generate_npc_encounter(player, map_data)
        elif event_type == "story":
            return await self._generate_story_event(player, map_data)
        elif event_type == "puzzle":
            return await self._generate_puzzle_event(player, map_data)
        elif event_type == "trap":
            return await self._generate_trap_event(player, map_data)
        elif event_type == "scenery":
            return await self._generate_scenery_event(player, map_data)
    
    async def _generate_npc_encounter(self, player, map_data):
        """NPC 遭遇 — 这是让游戏"活"起来的关键"""
        
        # 从地图NPC池中选择
        npc = self._select_npc(map_data, player)
        
        # 根据NPC性格、与玩家的关系、当前剧情进度生成对话
        dialogue = await self.ai_dialogue.generate(
            npc=npc,
            player=player,
            relationship=await self.get_relationship(player.id, npc["id"]),
            world_state=await self.get_world_state(),
            prompt_template="""
            你是{npc_name}，{npc_description}。
            当前场景：{location}
            你的性格：{personality}
            与对方关系：{relationship}（好感度{affinity}/100）
            
            对方（{player_name}）是{player_realm}修为的修士。
            
            用2-3句话与对方打招呼或互动，要符合修仙世界的语言风格。
            如果好感度高，态度要亲切；如果低，态度要冷淡或警惕。
            可能会提供线索、交易机会或请求帮助。
            """
        )
        
        return ExploreResult(
            type="npc_encounter",
            narrative=dialogue,
            choices=[
                {"text": "交谈", "action": "npc_talk", "params": {"npc_id": npc["id"]}},
                {"text": "交易", "action": "npc_trade", "params": {"npc_id": npc["id"]}},
                {"text": "请教修炼", "action": "npc_teach", "params": {"npc_id": npc["id"]}},
                {"text": "离开", "action": "leave"},
            ]
        )
```

### 4.4 小事件示例库（探索触发）

```json
{
  "random_events": {
    "canglan_city": [
      {
        "id": "street_vendor",
        "name": "神秘摊贩",
        "weight": 15,
        "narrative": "你在城中闲逛时，注意到一个戴着斗笠的老人在街角摆了个小摊。摊上只有三样东西，每样都蒙着布。老人嘶哑地说：「选一个吧，小友。看你的缘法。」",
        "choices": [
          {
            "text": "选左边的",
            "results": [
              {"weight": 50, "type": "item", "item": "low_spirit_herb", "narr": "你揭开布，是一株普通的灵草。老人笑道：「缘法一般。」"},
              {"weight": 30, "type": "item", "item": "mystery_scroll", "narr": "竟然是一卷古旧的功法残页！老人微微点头：「有些缘法。」"},
              {"weight": 20, "type": "item", "item": "rare_pearl", "narr": "一颗散发柔光的珠子！你感到鸿蒙珠在共鸣。老人猛然抬头看你，随即消失在人群中……"}
            ]
          },
          {
            "text": "选中间的", "results": ["..."]
          },
          {
            "text": "选右边的", "results": ["..."]
          },
          {
            "text": "不选，转身离开",
            "results": [
              {"weight": 100, "type": "mentality", "value": 3, "narr": "你不为所动，转身离去。身后传来老人的笑声：「不贪，好。」你感到心境更加通透。"}
            ]
          }
        ],
        "condition": {"min_realm": 1, "max_realm": 10, "cooldown_days": 7}
      },
      {
        "id": "falling_star",
        "name": "流星坠落",
        "weight": 3,
        "narrative": "夜晚，一颗流星拖着长长的尾焰从天际划过——但它没有消失，而是坠落在城外的山林中！\n\n一阵强烈的灵力波动从坠落点传来……",
        "choices": [
          {
            "text": "🏃 立刻前往查看",
            "results": [
              {"weight": 40, "type": "event_chain", "event": "meteor_dungeon", "narr": "你第一个赶到现场，发现了一个散发着星光的陨石坑……"},
              {"weight": 30, "type": "combat", "enemy": "star_beast_lv1", "narr": "还没靠近，一头浑身流光的异兽从坑中跃出！"},
              {"weight": 30, "type": "treasure", "item": "star_fragment", "narr": "陨石坑中，一块散发着温热的星辰碎片静静躺着。你感到衍道亲和在上升。"}
            ]
          },
          {
            "text": "🔭 先远远观察",
            "results": [
              {"weight": 60, "type": "info", "narr": "你在远处观察，看到好几拨修士争先恐后赶去。很快那里爆发了战斗……不过你也看清了坠落物的方位，记在了心里。"},
              {"weight": 40, "type": "item", "item": "star_dust", "narr": "在外围，你捡到了几粒散落的星辰碎屑。虽然不如核心珍贵，但也是难得之物。"}
            ]
          },
          {
            "text": "😴 与我无关，继续修炼",
            "results": [
              {"weight": 70, "type": "mentality", "value": 5, "narr": "你心如止水，不为外物所动。这份定力让你的心境更加稳固。"},
              {"weight": 30, "type": "hidden_flag", "flag": "missed_meteor_1", "narr": "你继续修炼……但你不知道的是，那颗流星中藏着的东西，日后将与你产生奇妙的因果。"}
            ]
          }
        ]
      }
    ]
  }
}
```

### 4.5 中事件 —— 支线任务链

```python
# 支线任务示例：药园守护

QUEST_HERB_GARDEN = {
    "id": "herb_garden_guardian",
    "name": "灵药园的烦恼",
    "trigger": {
        "type": "npc_affinity",
        "npc": "elder_chen",
        "min_affinity": 30,
        "min_realm": "jiedan"
    },
    "stages": [
        {
            "id": "stage_1",
            "narrative": """
陈长老面色凝重地找到你：

「{player_name}，老夫有一事相求。宗门后山的灵药园
最近总是遭到不明妖兽的偷袭，已经损失了好几株
百年灵药。你能否帮忙守护三天？」
            """,
            "choices": [
                {"text": "义不容辞", "next": "stage_2a", "affinity": +10},
                {"text": "需要报酬", "next": "stage_2b", "affinity": -5},
                {"text": "没空", "next": None}  # 拒绝任务
            ]
        },
        {
            "id": "stage_2a",
            "type": "timed_task",
            "duration": 3600 * 3,  # 现实3小时 = 游戏3天
            "check_events": [
                {"time": 3600, "event": "first_night_attack"},    # 1小时后触发
                {"time": 7200, "event": "second_night_clue"},     # 2小时后
                {"time": 10800, "event": "final_confrontation"}   # 3小时后
            ]
        },
        {
            "id": "first_night_attack",
            "narrative": """
第一夜——

月光下，药园的防护阵法突然泛起涟漪。
你猛然睁开眼，只见三只灵猫大小的暗色妖兽
正试图挖掘围墙下方的土壤。

它们的速度极快！
            """,
            "type": "combat",
            "enemies": [
                {"name": "暗蚁兽", "level": "auto_scale", "count": 3}
            ],
            "victory_next": "first_night_clue",
            "defeat_next": "quest_fail_recover"
        },
        {
            "id": "first_night_clue",
            "narrative": """
击退妖兽后，你检查了它们的尸体。

奇怪……这些妖兽身上有人为操控的痕迹——
它们的脑后各有一枚极细的灵针！

有人在幕后操纵。

你拔下灵针仔细查看，上面残留着微弱的灵力
波动……这种手法，像是某种傀儡术。
            """,
            "choices": [
                {"text": "🔍 追踪灵针的灵力波动", "next": "track_clue", "check": "spirit > 50"},
                {"text": "📋 向陈长老汇报", "next": "report_elder"},
                {"text": "🕐 继续守夜，等对方再来", "next": "second_night_clue"}
            ]
        },
        # ... 更多阶段，最终揭示是宗门内部的叛徒
    ],
    "rewards": {
        "basic": {"spirit_stones": 5000, "exp": 2000},
        "perfect": {"item": "century_spirit_herb", "skill_scroll": "puppet_detection"},
        "hidden": {"npc_unlock": "shadow_merchant", "flag": "sect_traitor_aware"}
    }
}
```

### 4.6 大事件 —— 世界事件系统

```python
class WorldEventSystem:
    """
    世界事件：所有在线玩家共同参与的事件
    这是TG群组游戏的核心社交玩法
    """
    
    # ===== 事件类型 =====
    
    WORLD_EVENTS = {
        "beast_tide": {
            "name": "🐉 妖兽潮",
            "description": "蛮荒深处的妖兽大规模出动，向苍澜城涌来！",
            "duration": 86400,  # 24小时
            "mechanic": "collective_boss",
            "boss_hp": "根据活跃玩家数 × 10000",
            "phases": [
                {
                    "name": "前锋：低阶妖兽群",
                    "hp_threshold": "75%",
                    "narrative": "城外出现了大量低阶妖兽，城防军正在抵抗！",
                    "min_realm_to_contribute": 1
                },
                {
                    "name": "主力：高阶妖兽",
                    "hp_threshold": "40%",
                    "narrative": "结丹级妖兽出现了！城墙开始出现裂痕！",
                    "min_realm_to_contribute": 5
                },
                {
                    "name": "BOSS：妖兽首领",
                    "hp_threshold": "10%",
                    "narrative": "天空阴云密布，一头元婴级大妖从云层中降下！",
                    "min_realm_to_contribute": 8
                }
            ],
            "rewards": {
                "participation": {"spirit_stones": 1000, "exp_multiplier": 1.5},
                "top_10": {"item": "beast_core_epic"},
                "mvp": {"title": "🛡️ 守城英雄", "item": "beast_king_inner_core"}
            },
            "failure_consequence": {
                "narrative": "苍澜城沦陷！所有玩家被迫转移到天渊洲避难。",
                "effect": "map_locked:canglan_city:72h"
            }
        },
        
        "secret_realm": {
            "name": "🌀 秘境开启",
            "description": "星陨海深处的上古秘境入口再次出现！",
            "duration": 43200,  # 12小时
            "mechanic": "instance_dungeon",
            "max_players": 50,
            "entry_cost": {"spirit_stones": 500},
            "floors": 10,
            "narrative_per_floor": True  # 每层AI生成独特描述
        },
        
        "auction": {
            "name": "🏛️ 百年大拍卖",
            "description": "万宝楼百年一度的大拍卖会即将开始！",
            "duration": 7200,  # 2小时（实时拍卖）
            "mechanic": "live_auction",
            "items": ["dynamic_based_on_server_progress"]
        },
        
        "celestial_phenomenon": {
            "name": "🌌 天象异变",
            "description": "天空出现三色极光，灵气浓度暴增！",
            "duration": 14400,  # 4小时
            "mechanic": "buff_event",
            "effect": {
                "cultivation_exp_multiplier": 3.0,
                "breakthrough_rate_bonus": 0.15,
                "special": "有极小概率顿悟"
            }
        }
    }
    
    async def trigger_world_event(self, event_id: str):
        """触发世界事件"""
        event = self.WORLD_EVENTS[event_id]
        
        # 1. 全服广播
        await self.broadcast_all(
            f"═══════════════════════\n"
            f"⚠️ 世界事件触发！\n"
            f"{event['name']}\n"
            f"─────────────────────\n"
            f"{event['description']}\n"
            f"⏱️ 持续时间：{event['duration'] // 3600}小时\n"
            f"═══════════════════════"
        )
        
        # 2. 存入世界状态
        await self.set_world_state("current_event", {
            "id": event_id,
            "start_time": time.time(),
            "end_time": time.time() + event["duration"],
            "data": event
        })
        
        # 3. 注册定时检查
        self.scheduler.add_job(
            self.check_event_progress, 
            'interval', 
            seconds=300,  # 每5分钟检查一次
            id=f"event_{event_id}",
            args=[event_id]
        )
```

### 4.7 群组内世界事件展示

```
═══════════════════════════════════════
⚠️ 【世界事件】妖兽潮来袭！
═══════════════════════════════════════

🐉 妖兽大军正在进攻苍澜城！

━━━━ 妖兽首领·血眼狼王 ━━━━
❤️ HP: ██████████░░░░ 724,500/1,000,000

📊 全服参战数据：
  ⚔️ 参战人数：47 人
  💥 总伤害：275,500
  🏆 当前MVP：剑二十三（伤害：32,400）

━━━━ TOP 5 ━━━━━━━━━━━━━
1. ⚔️ 剑二十三    32,400
2. ⚔️ 不动明王    28,100
3. ⚔️ 清风道人    24,800
4. ⚔️ 小白兔      21,300
5. ⚔️ 摸鱼仙人    18,600

⏱️ 剩余时间：6小时32分
═══════════════════════════════════════

[⚔️ 参战！] [📊 查看详情] [🏃 撤退]
```

---

## 第五章：让机器人「活」起来的 7 大核心技术

### 5.1 核心哲学

```
死的机器人：玩家操作 → 固定回复
活的机器人：玩家操作 → 世界状态变化 → 上下文感知回复 → 余韵

关键公式：
感觉活 = 变化感 + 记忆感 + 意外感 + 情感共鸣
```

### 技术一：上下文感知叙事引擎

```python
class ContextAwareNarrator:
    """
    不是简单的模板填充，而是理解当前「场景」后生成文本
    """
    
    async def generate_cultivation_narrative(self, player, result):
        """修炼叙事生成"""
        
        # 收集上下文
        context = {
            "player_name": player.name,
            "realm": REALMS[player.realm]["name"],
            "current_skill": player.active_skill.name,
            "location": MAPS[player.current_map]["description"],
            "time_of_day": self._get_game_time(),      # 游戏内时间
            "weather": await self._get_weather(),        # 游戏内天气
            "recent_events": await self._get_recent_events(player.id, limit=3),
            "mentality": player.mentality,
            "breakthrough_progress": player.realm_exp / player.realm_exp_max,
            "consecutive_cultivations": await self._get_consecutive_count(player.id),
            "world_event": await self._get_active_world_event(),
        }
        
        # 选择叙事策略
        strategy = self._select_strategy(context)
        
        if strategy == "normal":
            # 从预写模板池中选择（快速，不调AI）
            return self._template_narration(context, result)
        
        elif strategy == "special":
            # 特殊情况调用AI（顿悟、走火入魔、接近突破等）
            return await self._ai_narration(context, result)
        
        elif strategy == "milestone":
            # 里程碑时刻（突破、首次到达新区域等）—— 必须调AI
            return await self._ai_milestone_narration(context, result)
    
    def _select_strategy(self, ctx) -> str:
        """决定是否需要AI生成"""
        # 以下情况使用AI生成（更丰富的叙事）
        if ctx["breakthrough_progress"] > 0.95:
            return "special"  # 快要突破了
        if ctx["mentality"] < 30:
            return "special"  # 心境很低，可能走火入魔
        if ctx["consecutive_cultivations"] > 10:
            return "special"  # 连续修炼多次，需要变化
        if ctx["world_event"]:
            return "special"  # 有世界事件，叙事需要呼应
        return "normal"
    
    def _template_narration(self, ctx, result) -> str:
        """模板叙事 —— 高效但不重复"""
        
        # 关键：模板池足够大 + 组合变化
        
        # 开头（根据时间/天气/地点变化）
        openings = {
            ("morning", "sunny"): [
                "晨光透过窗棂，洒在你的身上。",
                "清晨的第一缕灵气格外清新。",
                "旭日初升，你开始了新一天的修行。",
            ],
            ("night", "rainy"): [
                "雨夜，灵气中带着丝丝水属性。",
                "淅沥的雨声中，你沉入修炼的寂静。",
                "雨水顺着屋檐滴落，仿佛天地也在修行。",
            ],
            # ... 更多组合
        }
        
        # 过程（根据功法类型变化）
        processes = {
            "heng_dao": [
                "灵气沿着经脉平稳运行，太清养气诀的口诀在心中流转。",
                "你一呼一吸间，周围灵气缓缓汇聚。",
            ],
            "ni_dao": [
                "体内灵力如逆流而上的激流，冲刷着每一条经脉。",
                "逆天诀的运转带来阵阵刺痛，但你甘之如饴。",
            ],
            # ...
        }
        
        # 结尾（根据修为进度变化）
        endings_by_progress = {
            (0, 0.3): [
                "虽然进境缓慢，但根基在稳步夯实。",
                "道阻且长，你不急不躁。",
            ],
            (0.3, 0.7): [
                "你能感到瓶颈在松动。",
                "灵力在丹田中越发充盈。",
            ],
            (0.7, 0.95): [
                "瓶颈近在咫尺！再加把劲！",
                "你隐约触摸到了下一个境界的门槛。",
            ],
            (0.95, 1.0): [
                "突破就在眼前！你能感到那层屏障薄如蝉翼！",
                "丹田中的灵力已经满溢，只差临门一脚！",
            ],
        }
        
        # 组合
        time_weather = (ctx["time_of_day"], ctx["weather"])
        opening = random.choice(openings.get(time_weather, openings[("morning", "sunny")]))
        
        skill_type = ctx["current_skill_type"]
        process = random.choice(processes.get(skill_type, processes["heng_dao"]))
        
        progress = ctx["breakthrough_progress"]
        for (low, high), endings in endings_by_progress.items():
            if low <= progress < high:
                ending = random.choice(endings)
                break
        
        return f"{opening}\n\n{process}\n\n{ending}"
```

### 技术二：记忆系统（让 NPC 记住你）

```python
class NPCMemorySystem:
    """
    NPC 记住与玩家的互动历史
    这是让游戏"活"的最关键技术
    """
    
    async def get_npc_memory(self, npc_id: str, player_id: int) -> dict:
        """获取 NPC 对某玩家的记忆"""
        
        memory = await self.db.fetchone("""
            SELECT * FROM npc_memories 
            WHERE npc_id = $1 AND player_id = $2
        """, npc_id, player_id)
        
        if not memory:
            return {
                "first_met": False,
                "affinity": 0,
                "interactions": [],
                "flags": {},
                "impression": "陌生人"
            }
        
        return memory
    
    async def update_memory(self, npc_id, player_id, interaction):
        """更新记忆"""
        memory = await self.get_npc_memory(npc_id, player_id)
        
        memory["interactions"].append({
            "time": datetime.now().isoformat(),
            "type": interaction["type"],
            "summary": interaction["summary"],
            "player_realm_at_time": interaction["player_realm"],
        })
        
        # 只保留最近 20 条互动
        memory["interactions"] = memory["interactions"][-20:]
        
        # 更新好感度
        memory["affinity"] = max(-100, min(100, 
            memory["affinity"] + interaction.get("affinity_change", 0)))
        
        # 更新印象（关键！）
        memory["impression"] = self._calc_impression(memory)
        
        await self.db.execute("""
            INSERT INTO npc_memories (npc_id, player_id, data) 
            VALUES ($1, $2, $3)
            ON CONFLICT (npc_id, player_id) DO UPDATE SET data = $3
        """, npc_id, player_id, json.dumps(memory))
    
    def _calc_impression(self, memory) -> str:
        """根据历史互动计算NPC对玩家的印象"""
        affinity = memory["affinity"]
        interactions = memory["interactions"]
        
        if affinity > 80:
            return "至交好友"
        elif affinity > 50:
            return "值得信赖的道友"
        elif affinity > 20:
            return "还算不错的年轻人"
        elif affinity > 0:
            return "有过几面之缘"
        elif affinity > -30:
            return "不太待见的家伙"
        else:
            return "仇人"


# 使用记忆生成对话
class NPCDialogueGenerator:
    
    async def generate(self, npc, player, memory) -> str:
        
        if not memory["first_met"]:
            # 第一次见面
            return await self._first_meeting(npc, player)
        
        # 有记忆的对话
        prompt = f"""
你是 {npc['name']}，{npc['personality']}。
你对 {player.name} 的印象是：{memory['impression']}（好感度：{memory['affinity']}）

最近的互动记录：
{self._format_recent_interactions(memory['interactions'][-5:])}

现在 {player.name} 再次出现在你面前。
请用1-3句修仙风格的话与他互动。

要求：
- 如果之前他帮过你，要表达感谢或提供回报
- 如果之前有过冲突，态度要谨慎或敌对
- 适当提及之前的互动（让玩家感到被记住）
- 可以根据玩家境界变化表达惊讶（如果他升级了很多）
"""
        
        return await self.ai.generate(prompt)
```

**实际效果示例：**

```
第一次遇到陈长老：

陈长老上下打量了你一眼，微微点头：
「新来的弟子？看着倒是个老实的。好好修行，
  莫要惹是生非。」

第五次遇到（帮他做过任务后）：

陈长老见到你，脸上露出笑意：
「是{player_name}啊！上次药园的事多亏了你，
  那几株灵药可是保住了。来来来，老夫最近得了
  壶好茶，陪老夫喝一杯如何？」
  
  💡 好感度足够，解锁新对话选项：
  [🍵 喝茶聊天] [📜 请教炼丹经验] [🎁 赠送礼物]

第十次遇到（你已经是元婴修士了）：

陈长老看到你时愣了一愣，随即大笑：
「好小子！当初那个结丹期的毛头小子，如今
  已经是元婴修士了！老夫当年果然没看错人。
  
  对了……有件事，也只有你这个境界的人才能帮忙了。」
  
  📋 解锁新任务：【长老的秘密】
```

### 技术三：时间感知系统（世界有昼夜四季）

```python
class GameTimeSystem:
    """
    游戏内时间系统
    现实 1 小时 = 游戏内 1 天
    现实 24 小时 = 游戏内 24 天 ≈ 1 个月
    现实 1 个月 = 游戏内 ~2 年
    """
    
    REAL_TO_GAME_RATIO = 24  # 1现实小时 = 24游戏小时
    
    def get_game_time(self) -> GameTime:
        """获取当前游戏内时间"""
        now = time.time()
        game_seconds = (now - self.EPOCH) * self.REAL_TO_GAME_RATIO
        
        return GameTime(
            year=int(game_seconds // (365 * 86400)) + 1,
            month=int((game_seconds % (365 * 86400)) // (30 * 86400)) + 1,
            day=int((game_seconds % (30 * 86400)) // 86400) + 1,
            hour=int((game_seconds % 86400) // 3600),
            season=self._get_season(game_seconds),
            time_of_day=self._get_time_of_day(game_seconds),
        )
    
    def _get_season(self, game_seconds) -> str:
        month = int((game_seconds % (365 * 86400)) // (30 * 86400)) + 1
        if month in (3, 4, 5): return "spring"    # 木属性灵气+20%
        if month in (6, 7, 8): return "summer"     # 火属性灵气+20%
        if month in (9, 10, 11): return "autumn"   # 金属性灵气+20%
        return "winter"                             # 水属性灵气+20%
    
    def _get_time_of_day(self, game_seconds) -> str:
        hour = int((game_seconds % 86400) // 3600)
        if 5 <= hour < 8: return "dawn"        # 阳气初生
        if 8 <= hour < 12: return "morning"    # 灵气平稳
        if 12 <= hour < 14: return "noon"      # 阳气最盛
        if 14 <= hour < 18: return "afternoon" # 灵气渐弱
        if 18 <= hour < 20: return "dusk"      # 阴阳交替（修炼效果±随机）
        if 20 <= hour < 23: return "evening"   # 阴气渐盛
        return "midnight"                       # 阴气最盛（逆道+20%）

# 在叙事中体现：
# 
# 黎明修炼：
# "卯时将至，东方泛起鱼肚白。你感到一股清新的阳气从天地间升起，
#  经脉中的灵力运转格外顺畅。（🌅 黎明加成：修炼效率 +10%）"
#
# 子夜修炼：  
# "子时三刻，万籁俱寂。浓郁的阴气从大地深处渗出，
#  你体内的逆天诀自动运转，贪婪地吞噬着这股力量。
#  （🌙 子夜 + 逆道功法加成：修炼效率 +25%）"
```

### 技术四：蝴蝶效应系统（选择有后果）

```python
class ButterflyEffectSystem:
    """
    玩家的每个选择都可能在未来产生影响
    这是让玩家觉得「这个世界是真的」的关键
    """
    
    # 标记系统：记录玩家做过的每个选择
    async def set_flag(self, player_id: int, flag: str, value: any = True):
        await self.db.execute("""
            INSERT INTO player_flags (player_id, flag, value, set_at)
            VALUES ($1, $2, $3, NOW())
            ON CONFLICT (player_id, flag) DO UPDATE SET value = $3
        """, player_id, flag, json.dumps(value))
    
    async def check_flag(self, player_id: int, flag: str) -> any:
        result = await self.db.fetchval("""
            SELECT value FROM player_flags WHERE player_id = $1 AND flag = $2
        """, player_id, flag)
        return json.loads(result) if result else None


# ========== 蝴蝶效应示例 ==========

# 在第一卷的流星事件中，玩家选择了"不去看"
# → 设置 flag: "missed_meteor_1" = True

# 30个游戏日后（约1.5现实小时后），触发后续：

DELAYED_EVENT_METEOR_CONSEQUENCE = {
    "trigger": {
        "type": "flag_check",
        "flag": "missed_meteor_1",
        "delay_game_days": 30,
    },
    "narrative": """
你在集市上听到几个修士在议论：

「听说了吗？上次那颗流星坠落的地方，
  有人找到了一块星辰铁！据说价值连城！」

「何止连城！那块星辰铁被铸成了一件灵器，
  现在正在万宝楼拍卖，起拍价五万灵石！」

你心中微微一动——如果当初自己去了的话……

不过转念一想，你因此多修炼了几个时辰，
心境也更加沉稳了。得失之间，自有因果。
    """,
    "effect": {
        "mentality": +3,
        "hidden_thought": "下次有机缘，要果断一些。"
    }
}

# 如果当初选了"去看"且成功获得星辰碎片：
DELAYED_EVENT_METEOR_PAYOFF = {
    "trigger": {
        "type": "flag_check",
        "flag": "got_star_fragment",
        "delay_game_days": 100,
    },
    "narrative": """
修炼时，你注意到储物袋中那块星辰碎片
突然散发出微弱的光芒——

它在共鸣！

与鸿蒙珠产生了某种联系！

你将碎片取出，放在鸿蒙珠旁边。两者之间
的光芒越来越盛，最终——

星辰碎片被鸿蒙珠吸收了！

鸿蒙珠的灵光比之前更亮了几分。
你感到衍道的感悟突然清晰了很多。
    """,
    "effect": {
        "dao_yan": +50,
        "pearl_level": "+1",
        "unlock": "star_sense_ability"
    }
}
```

### 技术五：动态难度调节（让每个玩家都有好体验）

```python
class DynamicDifficultySystem:
    """
    根据玩家的活跃度和水平动态调整难度
    让休闲玩家不觉得难，让硬核玩家不觉得无聊
    """
    
    async def get_player_profile(self, player_id: int) -> PlayerProfile:
        """分析玩家行为"""
        stats = await self.db.fetchone("""
            SELECT 
                COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours') as daily_actions,
                COUNT(*) FILTER (WHERE event_type = 'combat') as total_combats,
                AVG(CASE WHEN event_type = 'combat' THEN (result->>'won')::boolean::int END) as win_rate,
                COUNT(DISTINCT DATE(created_at)) as active_days
            FROM event_logs WHERE player_id = $1
        """, player_id)
        
        return PlayerProfile(
            play_style=self._classify_style(stats),  # casual/moderate/hardcore
            skill_level=self._estimate_skill(stats),  # low/medium/high
            daily_activity=stats["daily_actions"],
        )
    
    def adjust_encounter(self, encounter, profile):
        """调整遭遇难度"""
        
        if profile.play_style == "casual":
            # 休闲玩家：降低难度，增加叙事，减少惩罚
            encounter["enemy_hp"] *= 0.7
            encounter["enemy_attack"] *= 0.7
            encounter["failure_penalty"] *= 0.5
            encounter["reward"] *= 1.2  # 补偿
            encounter["narrative_detail"] = "detailed"
        
        elif profile.play_style == "hardcore":
            # 硬核玩家：增加难度，增加隐藏内容
            encounter["enemy_hp"] *= 1.3
            encounter["enemy_attack"] *= 1.2
            encounter["hidden_mechanic"] = True  # 解锁隐藏机制
            encounter["reward"] *= 1.5
            encounter["rare_drop_bonus"] = 0.1
        
        return encounter
```

### 技术六：离线成长系统（玩家不在也在成长）

```python
class OfflineSystem:
    """
    玩家不在线时，世界依然在运转
    下次登录时结算离线收益 + 告诉他错过了什么
    """
    
    async def settle_offline(self, player_id: int) -> OfflineReport:
        player = await self.get_player(player_id)
        
        offline_duration = time.time() - player.last_active.timestamp()
        game_days = int(offline_duration / 3600 * 24)  # 转换为游戏天数
        
        # 上限：最多结算48小时离线收益
        offline_duration = min(offline_duration, 172800)
        
        report = OfflineReport()
        
        # 1. 离线修炼收益（效率为在线的30%）
        if player.offline_action == "cultivate":
            sessions = int(offline_duration // self._get_cooldown(player.realm))
            per_session = self._calc_base_exp(player) * 0.3  # 30%效率
            total_exp = int(sessions * per_session)
            report.exp_gained = total_exp
        
        # 2. 离线期间发生的世界事件
        world_events = await self._get_world_events_during(
            player.last_active, datetime.now()
        )
        for event in world_events:
            report.missed_events.append({
                "name": event["name"],
                "outcome": event["outcome"],
                "was_affected": self._player_affected(player, event)
            })
        
        # 3. NPC 找过你
        npc_visits = await self._check_npc_visits(player_id, offline_duration)
        for visit in npc_visits:
            report.npc_messages.append(visit)
        
        # 4. 其他玩家互动
        social_events = await self._check_social_during_offline(player_id)
        report.social = social_events
        
        return report
    
    def format_offline_report(self, report, game_days) -> str:
        """生成离线报告文案"""
        
        text = f"""
═══════════════════════════════
📜 离线报告（游离了 {game_days} 天）
═══════════════════════════════

🧘 离线修炼：
  修为 +{report.exp_gained:,}（低效修炼模式）
"""
        
        if report.missed_events:
            text += "\n🌍 你不在的时候发生了：\n"
            for event in report.missed_events:
                text += f"  • {event['name']} — {event['outcome']}\n"
                if event['was_affected']:
                    text += f"    ⚠️ 这件事影响到了你！\n"
        
        if report.npc_messages:
            text += "\n💬 有人找过你：\n"
            for msg in report.npc_messages:
                text += f"  • {msg['npc_name']}：「{msg['message'][:30]}...」\n"
        
        text += "\n═══════════════════════════════"
        
        return text
```

**玩家登录看到的效果：**

```
═══════════════════════════════
📜 离线报告（游离了 156 天）
═══════════════════════════════

🧘 离线修炼：
  修为 +23,400（低效修炼模式）

🌍 你不在的时候发生了：
  • 🐉 妖兽潮进攻苍澜城 — 守城成功！
    ⚠️ 你的宗门"落霞谷"在战斗中出了力
  • 🌌 天象异变：三日灵雨 — 已结束
    可惜你错过了三倍修炼加成……

💬 有人找过你：
  • 陈长老：「{name}好久不见，老夫有事找你...」
  • 柳清竹：「你去哪了？我找了你好几天……」

⚔️ 社交动态：
  • "剑二十三" 向你发起了切磋请求（已过期）
  • 你的好友 "摸鱼仙人" 突破到了元婴期！

═══════════════════════════════

[📊 查看详情] [🧘 继续修炼] [💬 回复陈长老]
```

### 技术七：AI 驱动的动态叙事（最终武器）

```python
class AINarrator:
    """
    在关键时刻调用 AI 生成独一无二的叙事
    注意：不是每次都调用（太贵太慢），只在关键时刻
    """
    
    # AI 调用策略
    AI_TRIGGERS = {
        "always_ai": [
            "breakthrough_success",     # 突破成功
            "breakthrough_failure",     # 突破失败
            "first_visit_new_map",     # 首次到达新地图
            "major_story_event",       # 主线剧情
            "npc_deep_conversation",   # 与NPC深入对话
            "tribulation",             # 天劫
            "death_and_revival",       # 死亡与复活
        ],
        "sometimes_ai": [
            "rare_item_discovery",     # 发现稀有物品（50%概率用AI）
            "special_combat_moment",   # 战斗特殊时刻
            "enlightenment",           # 顿悟
        ],
        "never_ai": [
            "normal_cultivation",      # 普通修炼（用模板）
            "normal_combat",           # 普通战斗（用模板）
            "shop_interaction",        # 商店（用模板）
            "status_check",            # 查看状态（纯数据）
        ]
    }
    
    async def generate_story_moment(self, event_type: str, context: dict) -> str:
        """
        核心 AI 叙事生成
        """
        
        # 构建 prompt
        system_prompt = """
你是一个修仙世界的叙事者，负责为文字游戏生成沉浸式的叙事文本。

世界观基础：
- 这是一个融合了《凡人修仙传》《仙逆》《星辰变》的修仙世界
- 三道并存：恒道（积累）、逆道（逆天改命）、衍道（星辰造化）
- 主角拥有鸿蒙珠，身怀三道融合体质

写作风格要求：
- 修仙小说的典型文风，简洁有力
- 适量使用环境描写（2-3句）
- 关键时刻要有张力和画面感
- 每段回复控制在 100-200 字
- 不要说教，用画面说话
- 适当留白，给玩家想象空间
"""
        
        user_prompt = f"""
场景类型：{event_type}
玩家名：{context['player_name']}
当前境界：{context['realm']}
当前地点：{context['location']}
三道亲和：恒{context['dao_heng']}  逆{context['dao_ni']}  衍{context['dao_yan']}
心境：{context['mentality']}
近期经历：{context['recent_summary']}
具体情境：{context['specific_situation']}

请生成这个时刻的叙事文本。
"""
        
        response = await self.ai_client.chat(
            model="claude-sonnet-4-20250514",  # 或 deepseek-v3
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            max_tokens=300,
            temperature=0.8,  # 稍高的温度增加创意
        )
        
        return response.content
    
    # ===== AI 成本控制 =====
    
    async def generate_with_cache(self, event_type, context):
        """
        缓存策略：
        - 相似情境复用已有AI生成（改几个关键词）
        - 非关键时刻用模板
        - 每日每玩家 AI 调用上限 20 次
        """
        
        # 检查每日配额
        daily_count = await self.redis.incr(f"ai_quota:{context['player_id']}:{date.today()}")
        await self.redis.expire(f"ai_quota:{context['player_id']}:{date.today()}", 86400)
        
        if daily_count > 20:
            # 超过配额，降级为模板
            return self.template_fallback(event_type, context)
        
        # 检查缓存（相似场景）
        cache_key = f"ai_cache:{event_type}:{context['realm']}:{context['location']}"
        cached = await self.redis.get(cache_key)
        if cached and random.random() < 0.3:  # 30%概率复用缓存（稍作修改）
            return self._personalize_cached(cached, context)
        
        # 生成新的
        result = await self.generate_story_moment(event_type, context)
        
        # 存入缓存
        await self.redis.setex(cache_key, 3600, result)
        
        return result
```

---

## 第六章：战斗系统

### 6.1 回合制文字战斗

```python
class CombatEngine:
    """
    文字游戏的战斗不能像回合制RPG那样复杂
    但也不能简单到"自动战斗，显示结果"
    
    核心原则：
    1. 每回合 1-2 个选择（不超过 4 个按钮）
    2. 选择有策略性但不烧脑
    3. 战斗叙事要有画面感
    4. 控制在 3-8 回合内结束
    """
    
    async def start_combat(self, player_id, enemy_data) -> CombatState:
        player = await self.get_player(player_id)
        enemy = self._create_enemy(enemy_data, player)
        
        state = CombatState(
            player=player,
            enemy=enemy,
            round=0,
            log=[]
        )
        
        # 开场叙事
        opening = await self._generate_combat_opening(player, enemy)
        
        return state, opening
    
    async def process_action(self, state: CombatState, action: str) -> CombatRound:
        state.round += 1
        
        round_result = CombatRound()
        
        # 玩家行动
        if action == "attack":
            damage = self._calc_damage(state.player, state.enemy, "normal")
            state.enemy.hp -= damage
            round_result.player_action = f"你挥出一道灵力，击中了{state.enemy.name}！（-{damage} HP）"
            
        elif action == "skill":
            skill = state.player.active_combat_skill
            mp_cost = skill["mp_cost"]
            if state.player.mp >= mp_cost:
                state.player.mp -= mp_cost
                damage = self._calc_damage(state.player, state.enemy, "skill", skill)
                state.enemy.hp -= damage
                round_result.player_action = f"你催动{skill['name']}！{skill['combat_desc']}（-{damage} HP）"
            else:
                round_result.player_action = "灵力不足！你只能普通攻击。"
                damage = self._calc_damage(state.player, state.enemy, "normal") * 0.5
                state.enemy.hp -= damage
                
        elif action == "defend":
            state.player.defending = True
            round_result.player_action = "你运起灵力护体，严阵以待。（本回合防御 ×2）"
            
        elif action == "flee":
            flee_chance = self._calc_flee_chance(state.player, state.enemy)
            if random.random() < flee_chance:
                round_result.combat_end = True
                round_result.result = "fled"
                round_result.narrative = "你看准机会，施展身法脱离了战斗！"
                return round_result
            else:
                round_result.player_action = "你试图脱身，但被对方挡住了退路！"
        
        # 敌人行动（AI简单策略）
        if state.enemy.hp > 0:
            enemy_action = self._enemy_ai(state)
            round_result.enemy_action = enemy_action
        
        # 检查战斗结束
        if state.enemy.hp <= 0:
            round_result.combat_end = True
            round_result.result = "victory"
        elif state.player.hp <= 0:
            round_result.combat_end = True
            round_result.result = "defeat"
        
        return round_result


# 战斗 UI 展示

"""
⚔️ === 战斗 · 第 3 回合 === ⚔️

🧘 沈无极（结丹初期）
❤️ ████████░░ 680/850
💙 ████░░░░░░ 180/450

VS

🐺 三阶灵狼（结丹级）
❤️ ██████░░░░ 420/700

─────────────────────────────
📖 上回合：
你催动「太清剑诀」，一道金色剑气直劈而下！
灵狼侧身躲过要害，但左肩还是被削去一块皮肉。
(-185 HP)

灵狼怒嚎一声，血红的眼睛中凶光毕露，
猛然扑向你的咽喉！
你以灵盾勉强挡住，但被巨力震退三步。
(-120 HP)
─────────────────────────────

🎯 选择你的行动：

[⚔️ 普通攻击]     [🔮 太清剑诀(MP:80)]
[🛡️ 防御蓄力]     [🏃 尝试脱离]
"""
```

---

## 第七章：社交系统（TG群组特有优势）

### 7.1 群组玩法

```python
# TG 的优势：天然的群组生态

class SocialSystem:
    
    # ===== 切磋系统 =====
    async def challenge(self, challenger_id, target_id):
        """
        在群里 @对方 发起切磋
        群里所有人都能看到战况
        """
        pass
    
    # ===== 宗门系统（群组 = 宗门）=====
    async def create_sect(self, group_id, founder_id, sect_name):
        """
        一个TG群可以注册为一个宗门
        群主 = 掌门
        管理员 = 长老
        群员 = 弟子
        """
        pass
    
    # ===== 宗门战 =====
    async def sect_war(self, sect_a_id, sect_b_id):
        """
        宗门战：两个群的玩家进行团体对抗
        双方各出5名弟子，依次对战
        """
        pass
    
    # ===== 交易系统 =====
    async def player_trade(self, seller_id, buyer_id, item_id, price):
        """
        玩家之间交易
        群内可以摆摊（发交易消息）
        """
        pass
    
    # ===== 组队探索 =====
    async def team_explore(self, leader_id, member_ids, dungeon_id):
        """
        组队进入秘境
        需要不同的角色配置（输出/防御/辅助）
        """
        pass
```

### 7.2 群内互动展示

```
【群内消息】

🏛️ ════ 落霞谷 · 宗门广场 ════ 🏛️

⚡ @剑二十三 向 @摸鱼仙人 发起了切磋！

⚔️ 第一回合：
剑二十三祭出本命飞剑，一道青光直刺而去！
摸鱼仙人慌忙侧身——飞剑擦着他的衣袖划过。

「你小子，真来啊！」摸鱼仙人叫道。
「少废话，出招吧。」剑二十三冷冷道。

💬 围观弟子 @清风道人：打打打！
💬 围观弟子 @小白兔：摸鱼哥加油！
💬 围观弟子 @不动明王：我赌剑二十三赢

[📊 查看双方数据] [🎲 下注] [📢 喊话助威]
```

---

## 第八章：大纲 AI 化使用指南

### 8.1 可以直接给 AI 使用吗？

**可以，但需要分层处理：**

```
你的大纲文档
     │
     ├── 第一层：世界观总纲 ──→ 作为 System Prompt 的一部分
     │   （宇宙结构、三道本源、世界分层）
     │   用途：让 AI 理解世界观，所有生成都在这个框架内
     │
     ├── 第二层：境界 & 战力体系 ──→ 作为数据表存入数据库
     │   （14大境界、属性数值、突破条件）
     │   用途：游戏机制用数据驱动，不需要 AI 管
     │
     ├── 第三层：势力 & NPC ──→ 作为 JSON 配置文件
     │   （宗门、NPC、地图）
     │   用途：事件触发的条件和权重
     │
     ├── 第四层：主线剧情大纲 ──→ 作为剧情引擎的脚本
     │   （十卷故事大纲）
     │   用途：控制主线推进节奏
     │
     └── 第五层：细节文案 ──→ 由 AI 实时生成
         （每次修炼的描述、NPC对话、事件叙事）
         用途：保证每个玩家的体验独特
```

### 8.2 具体 Prompt 工程

```python
# ===== 世界观 System Prompt =====

WORLD_LORE_PROMPT = """
# 三界归源 · 世界设定

## 宇宙结构
鸿蒙未分之时，诞生三道本源意志：
- 恒道：时间·积累·因果（循序渐进，水滴石穿）
- 逆道：意志·破灭·重生（逆天改命，以战养战）
- 衍道：空间·造化·无限（星辰演化，开辟宇宙）

三道碰撞，炸开鸿蒙，形成万界树结构：
凡界 → 灵界 → 真界 → 仙界 → 神界 → 造化宇宙 → 鸿蒙本源

## 境界体系
炼气(1-15层) → 筑基(初/中/后/满) → 结丹 → 元婴 → 化神 
→ 炼虚 → 合体 → 大乘 → 渡劫 → 真仙 → 仙王 → 仙帝 
→ 神主 → 创世主宰 → 超脱者 → 鸿蒙道主

## 文风要求
- 修仙小说的经典文风
- 简洁有力，不啰嗦
- 画面感强，适量环境描写
- 保持神秘感和探索感

## 当前游戏状态
（以下由程序动态填充）
当前地图：{current_map}
当前季节：{season}
当前时辰：{time_of_day}
活跃世界事件：{world_event}
"""

# ===== NPC 个性化 Prompt =====

NPC_PROMPT_TEMPLATE = """
你是 {npc_name}。

身份：{npc_role}
性格：{personality}
说话方式：{speech_style}
当前心情：{mood}

与 {player_name} 的关系：{relationship}
好感度：{affinity}/100
记忆摘要：{memory_summary}

场景：{current_scene}

要求：
- 用1-3句话回应，符合你的性格
- 如果记得之前的互动，自然地提及
- 根据好感度调整语气
- 可以提供线索/任务/交易，但要符合你的角色
- 不要说出游戏机制相关的话（如"任务""经验值"）
"""

# ===== 事件叙事 Prompt =====

EVENT_NARRATIVE_PROMPT = """
为以下游戏事件生成叙事文本：

事件类型：{event_type}
事件名称：{event_name}
玩家：{player_name}（{realm}）
地点：{location}
具体情况：{situation}
玩家选择：{choices_available}

要求：
- 100-150字
- 设置悬念或选择困境
- 每个选择都应有合理的理由
- 不要透露"正确答案"
- 最后以省略号或悬念结尾
"""
```

### 8.3 文案分级策略（省钱关键）

```
文案来源分级：

Level 0: 纯模板（0成本）
├── 普通修炼叙事
├── 商店界面
├── 背包界面
├── 状态查看
└── 日常指令回复
占比：70%

Level 1: 模板 + 变量替换（0成本）
├── 带随机元素的修炼叙事
├── 微事件
├── 普通战斗叙事
└── 简单NPC对话
占比：20%

Level 2: AI 生成（有成本）
├── 突破叙事
├── 首次到达新区域
├── 重要NPC深度对话
├── 稀有事件
├── 主线剧情
└── 天劫 / 飞升
占比：10%

预估成本（1000 DAU）：
- Level 2 每次约 $0.002（deepseek-v3）
- 每人每天约 5 次 Level 2 = $0.01/人/天
- 1000 DAU × $0.01 = $10/天 = $300/月
- 用 DeepSeek 可降至 $30-50/月
```

---

## 第九章：完整玩家体验流程（前 30 分钟）

### 从 /start 到第一次突破

```
分钟 0-1:

玩家发送 /start

Bot:
═══════════════════════════════
🌌 三 界 归 源
═══════════════════════════════

混沌未开，鸿蒙未分。

三道本源在虚空中交织、碰撞……

而你，即将踏上一条前所未有的道路。

请输入你在这个世界中的名字：

─────────────────────────────

分钟 1-2:

玩家输入: 剑无痕

Bot:
苍澜洲，边陲小城。

一个名叫「剑无痕」的孤儿在破庙中醒来。
怀中紧紧攥着一颗灰暗无光的珠子——
那是养大你的老乞丐留下的唯一遗物。

今天，是城中「灵根测试」的日子。
所有十六岁的少年都要前往测试，
有灵根者可以加入修仙门派。

你摸了摸怀中的珠子，站起身来。

[🏃 前往灵根测试] [🔍 先看看珠子]

─────────────────────────────

分钟 2-3:

玩家选择: [🔍 先看看珠子]

Bot:
你将珠子取出，在晨光下仔细端详。

灰暗的表面毫无灵气波动——就是一颗普通的
石头珠子罢了。

但不知为何，每当你握着它的时候，
心中都会涌起一股莫名的安宁。

老乞丐临终前说过：
「小子，这珠子……比你想象的要值钱得多。
  等你有了灵气，再试试。」

有了灵气……前提是你得有灵根。

📌 获得道具：【灰暗珠子】
   （描述：一颗看起来毫不起眼的灰色珠子。
    但握在手中时会感到一丝温热。）

[🏃 前往灵根测试]

─────────────────────────────

分钟 3-5:

Bot:
城中广场上已经挤满了人。

一位白发老者坐在高台上——那是负责测试的
散修张老。他面前摆着一块闪闪发光的灵石。

「都排好队！一个一个来！」

你前面的少年伸手按上灵石，石头亮起明亮的
蓝光——

「水属性灵根！中等资质！可入落霞谷！」
人群中响起羡慕的声音。

轮到你了。

你深吸一口气，将手按上灵石——

……

灵石纹丝不动。

张老皱了皱眉：「再试试。」

你咬牙运力——灵石依然灰暗。

「废灵根。」张老摇了摇头。

人群中响起哄笑声。

📌 事件标记：废灵根判定

一个选择出现在你面前：

[😤 不甘心，恳求再测一次]
[😔 默默离开]  
[🤔 仔细观察灵石]

─────────────────────────────

分钟 5-7:

玩家选择: [🤔 仔细观察灵石]

Bot:
你没有急着离开，而是仔细看了看灵石。

在你触碰的那一刻，你的确感觉到了什么——
不是灵石在发光，而是怀中的珠子微微发烫了
一下。

就好像……珠子把灵石的反应给「吃」掉了？

这个念头刚出现就消散了。也许是你的错觉。

但你记住了这个细节。

📌 隐藏标记：「观察者」特质 +1
   （未来会触发更多观察类选项）
📌 隐藏标记：「珠子共鸣·一」

张老已经在催下一个人了。你只能离开广场。

没有灵根，就不能加入宗门。
但你不甘心就这么度过一生。

回到破庙，你思考着接下来该怎么办。

[📜 翻找老乞丐留下的遗物]
[🏃 去城外碰碰运气]
[🍵 去茶馆听听消息]

─────────────────────────────

分钟 7-10:

（一系列选择后，玩家获得第一部功法，
  开始修炼，感受到灵气——
  原来不是没有灵根，而是被珠子隐藏了）

分钟 10-15:

第一次修炼！

Bot:
🧘 你按照残页上的口诀，盘膝静坐。

「吸……呼……引天地灵气入体……」

起初什么也没发生。

但当你下意识握紧怀中的珠子时——

一丝极细微的凉意从珠子中渗出，顺着手臂
流入体内。

那是灵气！

虽然微弱得几乎感觉不到，但你确信——
那是灵气！

你不是废灵根！

泪水不知何时模糊了视线。

📊 修炼结果：
  ✅ 修为 +50（鸿蒙珠引导）
  ✅ 境界：炼气一层
  ✅ 恒道亲和 +5
  📈 突破进度：████░░░░░░ 5%

⏰ 下次修炼冷却：5分钟

🎉 成就解锁：【踏上仙途】
   "每个传奇，都始于微不足道的第一步。"

[🧘 继续修炼(4:52)] [📜 研究功法] [🗺️ 探索]

─────────────────────────────

分钟 15-25:

（玩家反复修炼 + 探索，触发各种微事件）
（修为逐渐积累，接近炼气二层）

分钟 25-30:

突破！

Bot:
你的修为终于达到了瓶颈！

丹田中的灵气满溢，仿佛要冲破某个无形的
屏障——

是突破的时刻了。

📊 突破：炼气一层 → 炼气二层
  基础成功率：90%
  悟性加成：+3%
  心境加成：+2%
  最终成功率：95%

  [⚡ 尝试突破！] [🧘 再积累一下]

玩家点击: [⚡ 尝试突破！]

（成功率95%，几乎必定成功 —— 这是新手引导的一部分）

Bot:
═══════════════════════════════
⚡ 突 破 ！
═══════════════════════════════

灵气在经脉中奔涌，你全力催动功法——

瓶颈如同一层薄膜，在灵力的冲击下
「啪」的一声碎裂！

一股温热的力量从丹田中涌出，
经脉拓宽了少许，灵力运转更加顺畅。

你缓缓睁开眼睛，嘴角露出一丝笑意。

虽然只是从炼气一层到二层——
最微不足道的进步。

但对你来说，这意味着一切。

🎉 恭喜！突破成功！
━━━━━━━━━━━━━━━━━━
📈 炼气一层 → 【炼气二层】
❤️ HP: 100 → 120
💙 MP: 50 → 60
⚔️ 攻击: 10 → 13
🛡️ 防御: 5 → 7

📌 新手提示：
   现在你可以挑战城外的低阶妖兽了！
   去「探索」看看吧。
═══════════════════════════════

[🗺️ 探索城外] [🧘 继续修炼] [📊 查看属性]
```

---

## 第十章：关键数值平衡表

### 10.1 境界突破时间表（控制节奏）

```
目标：让玩家有长期追求，但每个阶段都有可感知的进步

境界          所需现实时间      所需修炼次数    备注
─────────────────────────────────────────────────
炼气1→2       30分钟           3次           新手引导
炼气2→3       1小时            8次           学会探索
炼气3→5       3小时            20次          习惯循环
炼气5→10      1天              60次          开始遇到更多事件
炼气10→15     3天              150次         第一个真正瓶颈

筑基初        1周              ~300次        大里程碑！
筑基满        2周              ~600次        

结丹初        1个月            ~1500次       核心玩家留存点
结丹满        2个月            ~3000次       

元婴初        3-4个月          ~6000次       ★ 这是第一个飞升级爽点
元婴满        6个月            ~10000次      

化神初        8-10个月         ~15000次      凡界毕业
化神满        1年              ~20000次      准备飞升

飞升（渡劫）   1年+             ∞            终极挑战

注：以上假设玩家每天活跃30-60分钟
    充值/活动可以加速，但不应超过2倍
```

### 10.2 收益来源配比

```
修为获取来源占比（应保持的平衡）：

修炼（主动CD循环）     40%    ← 最稳定的来源
探索（随机事件）       25%    ← 惊喜感
战斗（历练刷怪）       20%    ← 需要投入精力
任务（主线/支线）      10%    ← 大块收益
活动（世界事件）        5%    ← 额外奖励

灵石获取来源：
日常任务              30%
探索/战斗掉落         30%
交易                  20%
活动/成就             20%

灵石消耗去向：
丹药（突破辅助）       40%    ← 最大消耗
功法（学习/升级）      20%
法器（装备）           20%
交易（社交消耗）       10%
复活/治疗             10%
```

---

## 第十一章：防沉迷与长期留存设计

### 11.1 每日循环设计

```
登录奖励（逐日递增，7日一循环）
     │
     ├── 日常任务（3-5个，30分钟可完成）
     │   ├── 修炼 3 次
     │   ├── 探索 2 次
     │   ├── 战斗 1 次
     │   ├── 与 NPC 对话 1 次
     │   └── 完成 1 个随机事件
     │
     ├── 挂机修炼（离线也能获得收益）
     │
     └── 随机惊喜（每天有 1 次特殊事件保底）

每周循环：
     ├── 周末大事件（世界事件）
     ├── 排行榜结算
     └── 宗门任务

每月循环：
     ├── 剧情主线推进
     ├── 秘境开启
     └── 百年大拍卖（游戏内百年）
```

### 11.2 防无聊机制

```
问题：中后期玩家修炼CD变长，容易无聊
解决：

1. 解锁副职业系统（结丹后）
   ├── 炼丹师：收集材料 → 炼丹（有成功/失败）
   ├── 炼器师：锻造装备
   ├── 阵法师：布置/破解阵法
   └── 驯兽师：捕获 & 培养灵宠

2. 解锁宗门管理（元婴后）
   ├── 收徒系统
   ├── 宗门建设
   └── 宗门秘境

3. 解锁跨服玩法（化神后）
   ├── 跨群组PVP
   ├── 跨群组世界BOSS
   └── 仙门大比

4. 内容更新节奏
   ├── 每周：新随机事件 2-3 个
   ├── 每月：新支线任务链 1 条
   └── 每季：新主线章节
```

---

## 最终总结：技术要点清单

```
✅ 核心架构
   □ Python + python-telegram-bot v20+ (async)
   □ PostgreSQL + Redis
   □ Docker 部署
   □ AI API 接入（DeepSeek/Claude）

✅ 让世界"活"的关键技术
   □ 上下文感知叙事（时间/天气/位置/状态影响文案）
   □ NPC 记忆系统（记住每个玩家的互动历史）
   □ 蝴蝶效应系统（选择有长远后果）
   □ 动态难度调节（根据玩家类型调整）
   □ 离线成长 + 世界持续运转
   □ AI 动态文本生成（关键时刻）
   □ 游戏内时间系统（昼夜四季）

✅ 玩家留存关键
   □ 前30分钟体验要流畅有代入感
   □ 每次操作都有叙事而非纯数据
   □ 微事件渗透到每个操作
   □ 选择有意义（影响后续发展）
   □ 社交玩法（群内PVP/组队/宗门）
   □ 离线也有收益
   □ 世界事件制造共同记忆

✅ 大纲使用方式
   □ 世界观 → System Prompt
   □ 境界数值 → 数据库/JSON
   □ 势力NPC → 配置文件
   □ 主线剧情 → 剧情引擎脚本
   □ 即时文案 → AI 实时生成 + 模板混合

✅ 开发优先级
   □ Phase 1 (2周): 基础框架 + 修炼 + 境界突破
   □ Phase 2 (2周): 探索 + 事件系统 + 战斗
   □ Phase 3 (2周): NPC + AI叙事 + 任务系统  
   □ Phase 4 (2周): 社交 + 宗门 + 世界事件
   □ Phase 5 (持续): 内容填充 + 平衡调整
```

> **先做一个能修炼、能突破、能探索的 MVP（最小可玩版本），然后用玩家反馈驱动迭代。技术再花哨，不如先让第一个玩家说出「卧槽，我还想再玩一会儿」。**







# 🌌 三界归源 · 千万字宏大世界设定总纲

> 融合《凡人修仙传》《仙逆》《星辰变》三大世界观，构建统一宇宙

---

## 第一卷【本源架构】— 宇宙总设定

### 一、宇宙起源：鸿蒙三柱说

太初之前，**鸿蒙未分**，无时间、无空间、无因果。

鸿蒙中诞生了三道**本源意志**（对应三部作品的终极法则）：

| 本源意志 | 对应核心           | 象征           | 原著映射               |
| -------- | ------------------ | -------------- | ---------------------- |
| **恒道** | 水滴石穿、凡人之道 | 时间·积累·因果 | 《凡人修仙传》韩立之道 |
| **逆道** | 逆天改命、万法归一 | 意志·破灭·重生 | 《仙逆》王林之道       |
| **衍道** | 星辰演化、宇宙创生 | 空间·造化·无限 | 《星辰变》秦羽之道     |

三道本源意志交织碰撞，**炸开鸿蒙**，诞生了：

```
鸿蒙大爆裂
    │
    ├── 【天道法则层】── 管理一切规则（天道、因果、轮回）
    │
    ├── 【万界树】── 承载所有位面的骨架
    │       │
    │       ├── 主干 ── 三千大世界（核心位面）
    │       ├── 枝干 ── 中千世界（过渡位面）
    │       └── 叶片 ── 小千世界（凡人界、低等修真界）
    │
    └── 【混沌海】── 万界树之外的无尽虚空（终极探索区）
```

---

### 二、世界分层地图（7 大层级，支撑区域解锁）

```
┌─────────────────────────────────────────────────┐
│           第七层：鸿蒙本源（终章区域）               │
│         ┌───────────────────────────────┐        │
│         │  第六层：造化宇宙（创世者领域）  │        │
│         │  ┌───────────────────────┐    │        │
│         │  │ 第五层：神界诸天        │    │        │
│         │  │ ┌─────────────────┐  │    │        │
│         │  │ │ 第四层：仙界四域  │  │    │        │
│         │  │ │ ┌───────────┐  │  │    │        │
│         │  │ │ │第三层：真界│  │  │    │        │
│         │  │ │ │┌───────┐ │  │  │    │        │
│         │  │ │ ││第二层 │ │  │  │    │        │
│         │  │ │ ││灵界上界│ │  │  │    │        │
│         │  │ │ ││┌────┐│ │  │  │    │        │
│         │  │ │ │││第一层│ │  │  │    │        │
│         │  │ │ │││凡界 ││ │  │  │    │        │
│         │  │ │ ││└────┘│ │  │  │    │        │
│         │  │ │ │└───────┘ │  │  │    │        │
│         │  │ │ └───────────┘  │  │    │        │
│         │  │ └─────────────────┘  │    │        │
│         │  └───────────────────────┘    │        │
│         └───────────────────────────────┘        │
└─────────────────────────────────────────────────┘
```

#### 详细地图设定：

---

### 第一层：凡界（卷 1-2 主战场 ｜ 约 200 万字）

| 区域       | 说明                                 | 对应原著元素        |
| ---------- | ------------------------------------ | ------------------- |
| **苍澜洲** | 主角出生地，类似韩立的元始，散修横行 | 《凡人》南疆+黄枫谷 |
| **天渊洲** | 宗门林立的正统修真大陆               | 《凡人》天南+乱星海 |
| **逆墟**   | 被天道遗弃的禁地，法则扭曲           | 《仙逆》赵国+各国   |
| **星陨海** | 星辰坠落之海，藏有上古遗迹           | 《星辰变》下界海域  |
| **蛮荒**   | 妖兽横行的原始大陆                   | 三书综合            |

**凡界特点：**
- 灵气稀薄，天材地宝稀少
- 最高只能修炼到**化神期**（天道压制）
- 飞升通道每千年开启一次
- 存在「界壁裂缝」可偶然窥见上界

---

### 第二层：灵界 / 上界（卷 3-4 主战场 ｜ 约 200 万字）

| 区域         | 说明                               |
| ------------ | ---------------------------------- |
| **天灵域**   | 人族核心领地，有灵界最大的宗门联盟 |
| **妖域**     | 妖族的领地，妖皇统治               |
| **鬼域**     | 亡灵与鬼修的世界，有轮回通道碎片   |
| **血域**     | 魔修与邪道的聚集地                 |
| **虚空裂谷** | 连接各域的危险通道，时空不稳定     |

**灵界特点：**
- 灵气浓郁百倍于凡界
- 最高可修至**大乘期**
- 存在种族战争（人、妖、魔、鬼四族）
- 渡劫飞升通往真界

---

### 第三层：真界（卷 5-6 主战场 ｜ 约 200 万字）

| 区域         | 说明                             |
| ------------ | -------------------------------- |
| **九天之域** | 真仙的领地，九大天域各有天尊     |
| **逆源之地** | 法则被逆转之地，一切规则颠倒     |
| **造化之墟** | 远古大能陨落之所，遍布机缘与死亡 |
| **命运长河** | 可窥视过去未来的禁地             |

**真界特点：**
- 法则可感可触，修士开始领悟「道」
- 仙人并非终点，只是新的起点
- 存在**天道意志**的直接干预
- 最高可修至**仙帝境**

---

### 第四层：仙界四域（卷 7-8 主战场 ｜ 约 150 万字）

| 域名       | 法则主题 | 统治者   |
| ---------- | -------- | -------- |
| **太初天** | 时间法则 | 太初仙帝 |
| **万象天** | 空间法则 | 万象仙帝 |
| **轮回天** | 生死法则 | 轮回仙帝 |
| **造化天** | 创生法则 | 造化仙帝 |

---

### 第五层：神界诸天（卷 8-9 ｜ 约 100 万字）

超越仙界，**以神道立身**。

| 神域         | 说明               |
| ------------ | ------------------ |
| **天神界**   | 光明正统神灵       |
| **冥神界**   | 掌管死亡与轮回     |
| **原始神界** | 最古老的神灵栖息地 |

---

### 第六层：造化宇宙（卷 9-10 ｜ 约 100 万字）

- 能够**开辟独立宇宙**的层次
- 类似《星辰变》秦羽创建宇宙的境界
- 每个造化主宰拥有自己的宇宙
- 主角在此面对**终极敌人**：试图吞噬万界树的「混沌主」

---

### 第七层：鸿蒙本源（终章 ｜ 约 50 万字）

- 回归三道本源
- 超越天道束缚
- 主角面对的终极命题：**宇宙的意义是什么？**

---

## 第二卷【修炼体系】— 完整境界设定

### 总境界架构（14 大境界 + 终极境）

```
════════════════════════════════════════════════════
  凡界篇          灵界篇         真界·仙界篇        神界·终极篇
════════════════════════════════════════════════════
  ① 炼气          ⑥ 炼虚          ⑩ 真仙            ⑬ 创世主宰
  ② 筑基          ⑦ 合体          ⑪ 仙王/仙帝        ⑭ 超脱者
  ③ 结丹          ⑧ 大乘          ⑫ 神主             ⑮ 鸿蒙道主
  ④ 元婴          ⑨ 渡劫飞升
  ⑤ 化神
════════════════════════════════════════════════════
```

### 详细境界说明：

---

#### 【凡界五境】

| 境界       | 细分                  | 核心突破点                         | 寿元         | 战力描述                   |
| ---------- | --------------------- | ---------------------------------- | ------------ | -------------------------- |
| **① 炼气** | 1-15 层               | 感应灵气，引气入体                 | 100-150 年   | 可御使法器，对抗数名武者   |
| **② 筑基** | 初期/中期/后期/大圆满 | 构筑灵力根基，灵根净化             | 200-300 年   | 飞行，操控数件法器         |
| **③ 结丹** | 初期/中期/后期/大圆满 | 灵力凝聚为金丹（丹的品质决定上限） | 400-500 年   | 可独斗小型妖兽群           |
| **④ 元婴** | 初期/中期/后期/大圆满 | 金丹碎裂，孕育元婴（第二生命）     | 800-1000 年  | 元婴可离体作战，一击碎山   |
| **⑤ 化神** | 初期/中期/后期/大圆满 | 元婴化神，初步触摸天地法则         | 2000-3000 年 | 操控部分天地之力，凡界巅峰 |

**突破核心机制 ——「瓶颈三要素」：**
```
突破 = 功法领悟（悟） + 资源消耗（财） + 心境契合（心）
                │              │              │
           需要功法对应     灵石、丹药、     心魔考验
           境界的口诀       天材地宝         （越高境界越难）
```

---

#### 【灵界四境】

| 境界       | 核心突破点                       | 寿元           | 特殊能力           |
| ---------- | -------------------------------- | -------------- | ------------------ |
| **⑥ 炼虚** | 化神之力与虚空融合，可撕裂空间   | 5000 年        | 虚空遁术、领域雏形 |
| **⑦ 合体** | 肉身与元神合一，天人合一之境     | 10000 年       | 领域展开、法则感应 |
| **⑧ 大乘** | 初步掌握一种法则（如风、火、雷） | 50000 年       | 法则之力、天地共鸣 |
| **⑨ 渡劫** | 承受天劫洗礼，脱胎换骨飞升       | 无尽（若飞升） | 渡过天劫即飞升真界 |

**灵界独有系统 ——「法则感悟」：**
```
基础法则（五行、风雷冰）
    ↓ 融合
高级法则（时间、空间、因果、命运）
    ↓ 至极
终极法则（生死、轮回、混沌）
```

每位修士最多感悟 **3 种基础法则 + 1 种高级法则**（天才上限）

---

#### 【仙界三境】

| 境界       | 细分                   | 核心                     | 寿元   |
| ---------- | ---------------------- | ------------------------ | ------ |
| **⑩ 真仙** | 地仙 / 天仙 / 太乙真仙 | 法则凝实，仙力取代灵力   | 百万年 |
| **⑪ 仙王** | 仙王 / 仙君 / 仙帝     | 法则融合，可创造小型空间 | 千万年 |
| **⑫ 神主** | 下位神 / 上位神 / 主神 | 超越法则，以「道」立身   | 亿年   |

---

#### 【终极三境】

| 境界           | 核心           | 说明                       |
| -------------- | -------------- | -------------------------- |
| **⑬ 创世主宰** | 开辟独立宇宙   | 如《星辰变》秦羽，可造世界 |
| **⑭ 超脱者**   | 超脱万界树束缚 | 进入混沌海，不受天道管辖   |
| **⑮ 鸿蒙道主** | 融合三道本源   | **全书终极境界**，亘古唯一 |

---

### 三大修炼路线（玩家 / 主角可选择）

```
┌──────────────────────────────────────────────────────────┐
│                     三大道途                               │
├──────────────┬──────────────────┬────────────────────────┤
│   恒道（正统）  │   逆道（叛逆）     │   衍道（造化）          │
├──────────────┼──────────────────┼────────────────────────┤
│ 循序渐进       │ 逆天改命          │ 星辰演化               │
│ 积累为王       │ 以战养战          │ 吞噬进化               │
│ 丹药辅助为主   │ 夺他人修为/气运   │ 炼化星辰之力           │
│ 稳定但慢       │ 快但有反噬风险    │ 需要特殊体质           │
├──────────────┼──────────────────┼────────────────────────┤
│ 代表功法：      │ 代表功法：         │ 代表功法：              │
│ 太清仙经       │ 逆天诀            │ 星辰变·造化篇          │
│ 纯阳无极功     │ 生死印            │ 万象星河决             │
│ 混元大道经     │ 轮回天经          │ 鸿蒙造化诀             │
├──────────────┼──────────────────┼────────────────────────┤
│ 优势：         │ 优势：            │ 优势：                  │
│ 根基扎实       │ 越级战斗能力强    │ 后期爆发力最强         │
│ 突破成功率高   │ 逆境突破概率高    │ 可吞噬万物为己用       │
│ 寿元最长       │ 心魔抵抗力强      │ 创造能力独一无二       │
├──────────────┼──────────────────┼────────────────────────┤
│ 劣势：         │ 劣势：            │ 劣势：                  │
│ 前期战力偏弱   │ 根基有暗伤风险    │ 前期极难入门           │
│ 需要大量资源   │ 因果纠缠         │ 需要特定星辰机缘       │
│ 突破周期长     │ 短寿（未化解时）  │ 中期瓶颈极大           │
└──────────────┴──────────────────┴────────────────────────┘
```

---

## 第三卷【功法·丹药·法宝体系】

### 功法品级

| 品级   | 层次        | 说明                     |
| ------ | ----------- | ------------------------ |
| 凡级   | 下/中/上/极 | 凡界流通，炼气至结丹可用 |
| 灵级   | 下/中/上/极 | 元婴以上才能修炼         |
| 仙级   | 下/中/上/极 | 飞升后的功法             |
| 神级   | 下/中/上/极 | 神主级存在的功法         |
| 造化级 | 无品        | 创世者级别，独一无二     |
| 鸿蒙级 | 无品        | 传说中的三卷鸿蒙天书     |

### 核心功法设定（30 部主要功法）

#### 恒道系列：
1. **太清养气诀** — 入门级，炼气专用，温和平稳
2. **纯阳无极功** — 筑基至元婴，阳属性，克制鬼物
3. **混元大道经** — 化神至合体，融合五行，均衡之道
4. **太初仙经** — 真仙级，时间法则入门
5. **恒道天书·上卷** — 鸿蒙级，主角最终功法之一

#### 逆道系列：
6. **逆天诀** — 入门即逆，每次突破需经历生死
7. **生死印** — 元婴级，生死法则雏形
8. **轮回天经** — 化神至大乘，可夺他人修为（有因果反噬）
9. **破灭仙诀** — 真仙级，一切法则在其面前破灭
10. **逆道天书·中卷** — 鸿蒙级

#### 衍道系列：
11. **星辰变** — 炼体入道，吸收星辰之力
12. **万象星河决** — 元婴级，以星河为引，演化万象
13. **造化神诀** — 仙王级，可创造生命
14. **鸿蒙造化诀** — 神主级，可开辟小世界
15. **衍道天书·下卷** — 鸿蒙级

#### 兼修/旁门：
16-30. 包括炼体功法、魂修功法、阵道功法、器道功法、丹道功法等各类支线功法

---

### 丹药体系

| 品级 | 代表丹药           | 效果                      |
| ---- | ------------------ | ------------------------- |
| 黄级 | 聚气丹、养血丹     | 辅助炼气修炼              |
| 玄级 | 筑基丹、破障丹     | 辅助筑基突破              |
| 地级 | 凝丹露、元婴果     | 辅助结丹/元婴             |
| 天级 | 化神丹、炼虚丸     | 辅助化神/炼虚（极其稀有） |
| 仙级 | 太乙仙丹、造化神丹 | 仙界才有的逆天丹药        |
| 神级 | 鸿蒙灵液           | 传说之物                  |

---

### 法宝品级

```
凡器 → 灵器 → 法宝 → 灵宝 → 仙器 → 神器 → 造化至宝 → 鸿蒙圣物
                                                              │
                                                    全书仅三件：
                                                    恒道之镜
                                                    逆道之印
                                                    衍道之珠
```

---

## 第四卷【势力架构】

### 凡界主要势力

```
┌─ 正道 ─────────────────────────────────┐
│  太清宗（第一大派，恒道传承）             │
│  天剑门（剑修圣地）                      │
│  丹鼎阁（丹道至尊）                      │
│  万法宗（博采众长）                      │
│  灵兽谷（驭兽世家）                      │
└──────────────────────────────────────────┘
┌─ 邪道 ─────────────────────────────────┐
│  逆天殿（逆道传承，亦正亦邪）            │
│  血煞宗（嗜血修炼）                      │
│  万鬼门（鬼修）                          │
│  天魔教（魔道至尊）                      │
└──────────────────────────────────────────┘
┌─ 散修/中立 ────────────────────────────┐
│  星辰阁（衍道传承，隐世不出）            │
│  乱星海散修联盟                          │
│  蛮荒妖族联盟                            │
│  商会·万宝楼                             │
└──────────────────────────────────────────┘
```

### 灵界势力（四大种族 + 隐世势力）

| 种族 | 核心势力                   | 特点                   |
| ---- | -------------------------- | ---------------------- |
| 人族 | 仙盟（七大超级宗门联合）   | 数量最多，内斗也多     |
| 妖族 | 妖庭（妖皇统治）           | 血脉传承，天赋强       |
| 魔族 | 魔渊（七大魔尊）           | 好战，修炼速度快但折寿 |
| 鬼族 | 幽冥界（鬼帝）             | 不死特性，擅长诅咒     |
| 隐世 | 远古世家（三道传承者后裔） | 守护秘密的古老家族     |

### 仙界势力

| 势力     | 级别     | 说明                     |
| -------- | -------- | ------------------------ |
| 四大天域 | 仙帝统治 | 太初/万象/轮回/造化 四天 |
| 天庭     | 名义最高 | 实际已衰落，名存实亡     |
| 三大禁地 | 超然物外 | 守护三卷鸿蒙天书的所在   |

---

## 第五卷【主角设定】

### 主角：沈无极

| 属性     | 设定                                                         |
| -------- | ------------------------------------------------------------ |
| 出身     | 苍澜洲边陲小城，孤儿，被老乞丐养大                           |
| 灵根     | 检测为「废灵根」（实际是三道融合体质，无法被常规手段检测）   |
| 性格     | 前期隐忍谨慎（韩立式），中期逆境爆发（王林式），后期从容造化（秦羽式） |
| 核心矛盾 | 身怀三道本源却不自知，被当作废物，逐步觉醒                   |
| 金手指   | **鸿蒙珠**（残破状态，随境界提升逐步修复）                   |

### 鸿蒙珠功能解锁：

| 阶段     | 功能                     | 境界要求 |
| -------- | ------------------------ | -------- |
| 残片     | 加速灵气吸收（2倍）      | 炼气     |
| 碎裂     | 开启内部空间（可种药）   | 筑基     |
| 缺损     | 法则感悟加速             | 元婴     |
| 半修复   | 时间加速（内部时间10:1） | 化神     |
| 大半修复 | 跨界感应                 | 大乘     |
| 近完整   | 预见命运碎片             | 仙王     |
| 完整     | 三道融合，开辟鸿蒙       | 超脱者   |

---

### 核心配角（12 人主要团队）

| 角色         | 定位              | 道途               | 与主角关系                     |
| ------------ | ----------------- | ------------------ | ------------------------------ |
| **柳清竹**   | 女主之一          | 恒道·丹道          | 青梅竹马（实为太清宗遗孤）     |
| **楚千殇**   | 女主之二          | 逆道·剑修          | 亦敌亦友，前世纠葛             |
| **星璇**     | 女主之三          | 衍道·天生星体      | 星辰阁圣女，宿命相连           |
| **韩苍**     | 兄弟              | 恒道·正统          | 憨厚老实的同门，后成大乘强者   |
| **王逆**     | 亦敌亦友          | 逆道·极端          | 逆天殿少主，与主角理念碰撞     |
| **秦星河**   | 兄弟              | 衍道·炼体          | 星辰阁弟子，热血单纯           |
| **墨无常**   | 导师              | 三道皆修（失败者） | 告诉主角三道融合的代价         |
| **幽冥鬼帝** | 前期大敌/后期盟友 | 鬼道               | 因果纠缠                       |
| **老乞丐**   | 隐藏导师          | 不明               | 养大主角的老人，真实身份是……   |
| **天道化身** | 终极对手之一      | 天道               | 天道意志的具象化               |
| **混沌主**   | 终极BOSS          | 混沌               | 万界树之外的存在，试图吞噬一切 |
| **小金**     | 灵宠              | 上古神兽血脉       | 从蛋开始孵化，陪伴全程         |

---

## 第六卷【故事大纲】— 千万字分卷规划

### 总体架构

```
10,000,000 字 ÷ 10 大卷 = 每卷约 100 万字
每卷约 300-400 章 × 3000 字/章
```

---

### 📖 第一卷「废灵根」（第 1-100 万字）

**核心词：隐忍·求生·炼气至筑基**

| 章节区间  | 剧情                                                         |
| --------- | ------------------------------------------------------------ |
| 1-50章    | 苍澜洲边城，孤儿沈无极被老乞丐养大，在灵根测试中被判定为废灵根，遭受嘲笑。老乞丐临终前将一枚灰暗的珠子（鸿蒙珠残片）交给他 |
| 51-100章  | 机缘巧合进入一个小宗门「落霞谷」做杂役弟子，发现鸿蒙珠能加速吸收灵气，偷偷修炼。炼气期在宗门属于最底层，饱受欺凌 |
| 101-150章 | 宗门试炼，进入「星陨秘境」，在其中发现上古修士洞府，获得第一部功法「太清养气诀」（恒道入门）。同时鸿蒙珠共鸣，意外激活了逆天诀的第一层 |
| 151-200章 | 筑基风波：资源不够，被迫以散修身份在乱星海历练赚取灵石。遇到柳清竹（被追杀的少女），出手相救，建立羁绊 |
| 200-280章 | 筑基成功！但发现自己的筑基与众不同——三色灵力交织。引起太清宗注意（正面）和逆天殿注意（觊觎）。第一次生死大战：逆天殿弟子追杀 |
| 280-330章 | 加入太清宗外门，在宗门中韬光养晦。暗线：老乞丐的身份之谜浮出水面（他留下的痕迹指向上古大能） |

**卷末高潮：** 太清宗与逆天殿爆发冲突，主角被卷入，筑基修为面对结丹敌人，危急时刻鸿蒙珠爆发，逆道之力觉醒，击退敌人但也暴露了自身的特殊性。

**本卷字数：约 100 万字**
**本卷主题：「蝼蚁也有翻天之志」**

---

### 📖 第二卷「破丹成婴」（第 100-200 万字）

**核心词：崛起·结盟·结丹至元婴**

| 章节区间  | 剧情                                                         |
| --------- | ------------------------------------------------------------ |
| 1-80章    | 太清宗内门试炼，主角结丹。丹的品质震惊所有人——三色金丹（前所未见）。正式成为内门弟子，获得更多资源 |
| 81-160章  | 天渊洲大比！各大宗门齐聚。主角代表太清宗参战，以结丹修为连胜元婴对手，名震天下。同时与王逆（逆天殿少主）首次正面交锋，两人理念碰撞 |
| 161-240章 | 上古遗迹开启——「鸿蒙战场」（远古大能的战场遗迹），各方势力争夺。主角在其中获得星辰变功法碎片，衍道觉醒！三道融合体质初步显现 |
| 241-330章 | 元婴突破！三色元婴，引发天象异变，惊动灵界大能下界窥探。主角感受到巨大压力，决定加速成长。同时，柳清竹的身世之谜揭开——她是太清宗祖师转世 |

**卷末高潮：** 蛮荒妖兽大举入侵天渊洲，化神级大妖领军。各宗门联合抵抗，主角以元婴修为击杀化神初期大妖，但自己也重伤。老乞丐的幻影在危机时刻出现，说了一句话："三道归一，方为至极。"

**本卷字数：约 100 万字**
**本卷主题：「天才与妖孽之间只差一个选择」**

---

### 📖 第三卷「化神之劫」（第 200-300 万字）

**核心词：心魔·背叛·化神**

| 主线     | 剧情要点                                                     |
| -------- | ------------------------------------------------------------ |
| 化神瓶颈 | 三道融合导致心魔格外强大，三次突破失败                       |
| 宗门内乱 | 太清宗叛徒勾结魔族，发动政变                                 |
| 逆境成长 | 主角被陷害，流落逆墟禁地，在法则扭曲之地反而领悟逆道真谛     |
| 化神突破 | 在生死边缘，三道心魔同时出现，主角以「恒心化逆境，逆境衍新生」的感悟一举突破 |
| 真相浮现 | 发现幕后黑手是一位灵界大能的分身，凡界不过是更大棋局的一颗棋子 |

**卷末高潮：** 主角化神成功，单人回到太清宗清理叛徒。化神巅峰战力碾压全场。但灵界大能的投影降临，一指将主角重伤，说："蝼蚁就该有蝼蚁的觉悟。"主角发下大誓："总有一日，我会亲手灭了你的本体。"

**本卷字数：约 100 万字**
**本卷主题：「心魔不在外，在我」**

---

### 📖 第四卷「飞升灵界」（第 300-400 万字）

**核心词：新世界·种族战争·炼虚至合体**

| 主线         | 剧情要点                                                     |
| ------------ | ------------------------------------------------------------ |
| 渡劫飞升     | 经历九重天劫，每一劫对应一种法则考验，最终飞升灵界           |
| 灵界求生     | 刚飞升的修士是最弱的，被灵界土著当猎物。从零开始在新世界立足 |
| 种族大战前奏 | 人妖魔鬼四族矛盾激化，主角被卷入                             |
| 合体突破     | 在种族战争的夹缝中，肉身与元神合一，领域「三道天域」成型     |
| 柳清竹重逢   | 她比主角更早飞升（太清祖师记忆觉醒），已是灵界大人物         |

**本卷字数：约 100 万字**
**本卷主题：「飞升不是终点，而是另一个起点」**

---

### 📖 第五卷「灵界风云」（第 400-500 万字）

**核心词：大乘·渡劫·灵界之巅**

| 主线         | 剧情要点                                                     |
| ------------ | ------------------------------------------------------------ |
| 七大宗门暗斗 | 仙盟内部权力斗争，各宗门为争夺飞升名额不惜代价               |
| 大乘突破     | 主角领悟时间法则（恒道）、破灭法则（逆道）、空间法则（衍道），三法则同修震古烁今 |
| 凡界回访     | 通过秘法短暂回到凡界，发现凡界已过千年，故人凋零             |
| 四族决战     | 魔族入侵，主角率人族反击，大乘巅峰的战斗改天换地             |
| 渡劫飞升真界 | 十二道天劫，史上最强天劫，连灵界天道都在颤抖                 |

**卷末高潮：** 渡劫时那位灵界大能正身出手阻止，与主角展开大乘巅峰对决。主角以三道融合之力重创对手，在天劫雷海中飞升真界。临走前，灵界天空出现三色极光，万族共仰。

**本卷字数：约 100 万字**
**本卷主题：「凡人也可一步登天」**

---

### 📖 第六卷「仙道之始」（第 500-600 万字）

**核心词：真仙·仙界格局·九天之域**

| 主线       | 剧情要点                                                 |
| ---------- | -------------------------------------------------------- |
| 真界适应   | 法则可视化，一切重新学习。真仙并非终点，而是仙道的起点   |
| 九天格局   | 四大天域各有仙帝，暗中博弈。天庭名存实亡                 |
| 楚千殇主线 | 第二女主楚千殇出现，她是逆道传承者，与主角宿命纠缠       |
| 仙王之路   | 从地仙到天仙到太乙真仙，再突破至仙王                     |
| 上古秘密   | 发现「三卷鸿蒙天书」的存在——恒道天书、逆道天书、衍道天书 |

**本卷字数：约 100 万字**
**本卷主题：「仙人？也不过是更强的凡人罢了」**

---

### 📖 第七卷「天书之争」（第 600-700 万字）

**核心词：仙帝·天书争夺·仙界大乱**

| 主线                 | 剧情要点                                                     |
| -------------------- | ------------------------------------------------------------ |
| 仙帝出手             | 四大仙帝联手封锁仙界，争夺天书                               |
| 主角获得恒道天书上卷 | 修为暴涨至仙帝境                                             |
| 仙界大乱             | 四大天域开战，整个仙界动荡                                   |
| 三道传承者齐聚       | 恒道（主角）、逆道（楚千殇/王逆）、衍道（星璇）三方博弈与合作 |
| 天道降世             | 天道化身出现，试图阻止任何人集齐三卷天书                     |

**卷末高潮：** 主角联合楚千殇和星璇，对抗天道化身。战斗规模毁灭数个星域。天道化身被击退，但说出惊天真相："集齐三卷天书者，要么成为新的天道，要么……被混沌吞噬。"

**本卷字数：约 100 万字**
**本卷主题：「天道无情，我便逆了这天道」**

---

### 📖 第八卷「神界之上」（第 700-800 万字）

**核心词：神主·神界·超越**

| 主线       | 剧情要点                                                     |
| ---------- | ------------------------------------------------------------ |
| 突入神界   | 仙帝巅峰突破至下位神，进入神界                               |
| 三大神界   | 天神界、冥神界、原始神界的三方格局                           |
| 主神级战斗 | 修为达到主神，领悟「道」的真谛                               |
| 老乞丐真相 | 终于揭开——他是上一纪元的超脱者残魂，为阻止混沌主而转世守护主角 |
| 混沌入侵   | 混沌海的力量开始侵蚀万界树，三千大世界有毁灭危机             |

**本卷字数：约 100 万字**
**本卷主题：「神也会死，道也会灭」**

---

### 📖 第九卷「创世之战」（第 800-900 万字）

**核心词：创世·造化·宇宙之战**

| 主线         | 剧情要点                                             |
| ------------ | ---------------------------------------------------- |
| 创世主宰     | 突破至创世主宰，开辟属于自己的宇宙                   |
| 集齐三卷天书 | 恒道天书、逆道天书、衍道天书合一                     |
| 混沌主降临   | 终极 BOSS 从混沌海降临，万界树开始枯萎               |
| 诸天联军     | 凡界、灵界、真界、仙界、神界所有旧友齐聚             |
| 超脱之战     | 主角突破至超脱者，与混沌主在万界树之外的混沌海中决战 |

**卷末高潮：** 史诗级决战。混沌主力量无穷，主角以三道融合之力堪堪抵挡。关键时刻，老乞丐的残魂最后一次出现，以自我牺牲为主角打开最后的突破契机。

**本卷字数：约 100 万字**
**本卷主题：「为了守护，可以牺牲一切」**

---

### 📖 第十卷「鸿蒙」（第 900-1000 万字）

**核心词：归一·终极·鸿蒙道主**

| 主线       | 剧情要点                                                     |
| ---------- | ------------------------------------------------------------ |
| 三道归一   | 恒道、逆道、衍道完美融合，达到亘古未有的境界                 |
| 击败混沌主 | 不是消灭，而是将其融入新的秩序                               |
| 重塑万界   | 以鸿蒙道主之力重塑万界树，赋予万界新的生机                   |
| 最终选择   | 成为新的天道（永恒但失去自我）还是放弃力量回归凡人           |
| 尾声       | 主角选择了第三条路——将力量化为种子播撒万界，自己以凡人之身重新开始。在苍澜洲的边城，一个老人捡到一颗灰暗的珠子，看着身边的孤儿微笑 |

**本卷字数：约 100 万字**
**本卷主题：「一切归于鸿蒙，一切重新开始」**

---

## 第七卷【游戏系统适配】

### RPG 数值框架

```
角色属性：
├── 基础属性
│   ├── 体魄（HP、物理防御）
│   ├── 灵力（MP、法术强度）
│   ├── 神识（感知、控制范围）
│   ├── 悟性（突破成功率、技能学习速度）
│   └── 气运（随机事件触发概率、掉落品质）
│
├── 修为值（EXP）
│   └── 每个境界需要固定修为值 + 突破任务
│
├── 三道亲和度
│   ├── 恒道值（0-100%）
│   ├── 逆道值（0-100%）
│   └── 衍道值（0-100%）
│   注：三道总和不限，但偏科越严重特殊效果越强
│
└── 心境值
    └── 影响突破成功率，被打击降低，顿悟提升
```

### 区域解锁条件

| 区域     | 解锁条件                  |
| -------- | ------------------------- |
| 苍澜洲   | 游戏开始                  |
| 天渊洲   | 筑基期 + 主线任务         |
| 逆墟     | 化神期 + 逆道值 > 30%     |
| 星陨海   | 元婴期 + 衍道值 > 30%     |
| 灵界     | 渡劫飞升                  |
| 真界     | 灵界渡劫                  |
| 仙界四域 | 真仙境                    |
| 神界     | 仙帝境                    |
| 混沌海   | 创世主宰境 + 集齐三卷天书 |

---

## 第八卷【核心冲突设计矩阵】

保证千万字不水的关键——**多层次冲突同时推进**：

```
┌─────────────────────────────────────────────────────────┐
│                    冲突层次                                │
├──────────┬──────────────────────────────────────────────┤
│ 个人层   │ 废灵根的自我证明 → 三道融合的代价 → 永恒vs凡人 │
├──────────┼──────────────────────────────────────────────┤
│ 关系层   │ 三女主的感情纠葛 → 兄弟的理念分歧 → 师徒的秘密 │
├──────────┼──────────────────────────────────────────────┤
│ 势力层   │ 宗门政治 → 种族战争 → 仙帝博弈 → 神界三分       │
├──────────┼──────────────────────────────────────────────┤
│ 世界层   │ 天道的压制 → 混沌的入侵 → 鸿蒙的真相            │
├──────────┼──────────────────────────────────────────────┤
│ 哲学层   │ 凡人vs仙人 → 顺天vs逆天 → 秩序vs自由            │
└──────────┴──────────────────────────────────────────────┘
```

---

## 附录：写作节奏控制表

| 字数段     | 节奏      | 爽点密度 | 说明                 |
| ---------- | --------- | -------- | -------------------- |
| 0-100万    | 慢热+蓄力 | ★★☆☆☆    | 世界观铺垫，读者代入 |
| 100-200万  | 加速      | ★★★☆☆    | 崛起爽感，连续打脸   |
| 200-300万  | 高潮+低谷 | ★★★★☆    | 背叛、心魔、绝地反击 |
| 300-400万  | 新篇章    | ★★★☆☆    | 新世界探索的新鲜感   |
| 400-500万  | 持续高压  | ★★★★☆    | 种族大战，史诗感     |
| 500-600万  | 再次蓄力  | ★★★☆☆    | 仙界新格局铺垫       |
| 600-700万  | 大高潮    | ★★★★★    | 天书争夺，多方混战   |
| 700-800万  | 解谜      | ★★★☆☆    | 真相揭露，伏笔收束   |
| 800-900万  | 终极高潮  | ★★★★★    | 创世之战，全员集结   |
| 900-1000万 | 收尾      | ★★★★☆    | 感动收束，开放结尾   |

---

> **这套设定可以直接用于：网文写作、RPG游戏剧本、Galgame剧情线、TRPG 战役设计。**
>



