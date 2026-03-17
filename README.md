# XiuXianBot - 修仙文字游戏后端

基于 Telegram 的修仙题材文字RPG游戏服务端。融合《凡人修仙传》、《仙逆》、《星辰变》三部经典修仙体系，构建"三界归源"宏大世界观。

## 技术栈

| 组件 | 方案 |
|------|------|
| 语言 | Python 3.13 |
| Web框架 | Flask |
| 数据库 | PostgreSQL (psycopg2 连接池) |
| 包管理 | uv (pyproject.toml) |
| TG适配 | python-telegram-bot 22.x |
| 部署 | Docker + Docker Compose |

## 快速开始

```bash
# 1. 安装 uv
pip install uv

# 2. 安装依赖
uv sync

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 填写 BOT_TOKEN、DATABASE_URL 等

# 4. 启动 PostgreSQL
# 确保 PG 运行在 localhost:5432

# 5. 启动服务
uv run python start.py
```

## 端口

| 服务 | 端口 |
|------|------|
| Core API | 11450 |
| 本地管理面板 | 11451 |
| 公网页面 | 11452 |

## 项目结构

```
XiuXianBot/
├── core/
│   ├── routes/          # API 路由 (combat, shop, sect, events, gacha, pvp...)
│   ├── services/        # 业务逻辑 (settlement, quests, gacha, events, pvp...)
│   ├── game/            # 游戏数据与引擎
│   │   ├── realms.py        # 境界体系 (32境界 + 三道亲和 + 心境系统)
│   │   ├── techniques.py    # 功法体系 (30部功法 + 丹药 + 法宝品级)
│   │   ├── maps.py          # 世界地图 (7层世界 + 27区域)
│   │   ├── events_engine.py # 事件引擎 (40+微事件 + 触发/条件系统)
│   │   ├── npcs.py          # NPC系统 (20个NPC + 好感度 + 记忆)
│   │   ├── combat.py        # 战斗系统 + 怪物定义
│   │   ├── skills.py        # 战斗技能
│   │   ├── items.py         # 物品/装备/词缀
│   │   ├── elements.py      # 五行相克
│   │   └── secret_realms.py # 秘境
│   ├── database/
│   │   ├── connection.py    # DB连接池 + 建表 + 事务
│   │   └── migrations.py    # 数据迁移
│   └── config.py            # 配置加载
├── adapters/            # Telegram 适配器
├── web_local/           # 本地管理面板
├── web_public/          # 公开 Web
├── tests/               # 150+ pytest 用例
├── outline/             # 设计文档
│   └── scripts.md       # 全技术设计文档 + 世界观大纲
├── pyproject.toml       # uv 项目配置
├── .env.example         # 环境变量模板
└── start.py             # 启动入口
```

## 核心系统

### 境界体系
- 14大境界(炼气→鸿蒙道主)，游戏内32个细分等级
- 三道亲和：恒道(正统)、逆道(叛逆)、衍道(造化)
- 心境系统：影响突破成功率、顿悟概率、走火入魔风险
- 突破三要素：功法领悟(悟) + 资源消耗(财) + 心境契合(心)

### 功法体系
- 6大品级：凡级 → 灵级 → 仙级 → 神级 → 造化级 → 鸿蒙级
- 30部核心功法(恒道5 + 逆道5 + 衍道5 + 旁门15)
- 16种丹药(黄/玄/地/天/仙/神)
- 8阶法宝(凡器→鸿蒙圣物)

### 世界地图
- 7层世界：凡界 → 灵界 → 真界 → 仙界 → 神界 → 造化宇宙 → 鸿蒙本源
- 27个可探索区域，按境界和道途亲和解锁
- 灵气浓度影响修炼效率

### 事件系统
- 微事件(40+)：修炼/探索/战斗中随机触发，让世界"活"起来
- 小事件/中事件/大事件/史诗事件：多层次内容架构
- 条件系统：地图、境界、道途、概率等多维判定

### NPC记忆系统
- 20个分布各地的NPC(故事/商人/任务/训练师)
- 好感度系统(仇敌→至交好友)
- 互动记忆存储

### 其他系统
- 五行相克战斗(金木水火土)
- 宗门系统(创建/管理/任务/转让)
- PvP竞技(匹配/排名/奖励)
- 抽卡系统(保底机制)
- 世界Boss
- 每日任务/成就系统
- 签到(月度里程碑)
- 锻造/分解

## 鉴权

- `X-Internal-Token`: 内部服务认证(必须)
- `X-Actor-User-Id`: 用户身份(业务接口)
- Body 中 `user_id` 必须与 `X-Actor-User-Id` 一致

## 测试

```bash
uv run python -m pytest -q
```

## 开发进度

### 已完成
- [x] 核心API框架 (Flask + 路由 + 鉴权)
- [x] SQLite → PostgreSQL 完整迁移
- [x] pip → uv 包管理迁移
- [x] 境界体系增强 (三道亲和 + 心境 + 突破三要素)
- [x] 功法/丹药/法宝数据体系
- [x] 7层世界地图 + 27区域
- [x] 事件引擎 (40+微事件)
- [x] NPC定义 + 记忆系统DB表
- [x] 战斗系统 (回合制 + 五行 + 精英词缀)
- [x] 宗门系统 (CRUD + 任务 + 转让)
- [x] PvP/抽卡/世界Boss
- [x] 每日任务/成就/签到
- [x] 150+ 测试用例

### 待办
- [ ] 功法修炼循环(CD + 顿悟 + 走火入魔)
- [ ] 突破系统重构(三要素判定 + 天劫)
- [ ] 地图移动 + 区域探索 API
- [ ] NPC对话交互 API
- [ ] 事件系统服务层(落库 + 触发集成)
- [ ] AI动态叙事引擎(Claude/DeepSeek)
- [ ] 时间感知系统(昼夜四季)
- [ ] 离线挂机系统
- [ ] Telegram Bot 适配器对接
- [ ] Docker Compose 部署配置
- [ ] Redis 缓存层
- [ ] 前30分钟新手引导流程

## 版本

当前版本: **0.1.52** (OSBLTSDocker0.1.52)

## License

Private
