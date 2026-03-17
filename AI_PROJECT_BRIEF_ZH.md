# XiuXianBot 项目说明（给第一次接手的 AI）

## 1. 项目定位
XiuXianBot 是一个“修仙题材”的后端游戏服务，核心是 Flask + SQLite。  
支持 Telegram 适配器、本地管理面板和公开 Web 页面。  
功能覆盖：注册、修炼、狩猎、秘境、装备、技能、商店、任务、PVP、宗门、炼丹、抽卡、成就、活动、资源转化、社交互动。

---

## 2. 技术与运行方式
### 技术栈
- Python 3.13
- Flask
- SQLite（WAL）
- pytest（150 用例）

### 入口文件
- `start.py`：一键启动 Core + 适配器 + Web
- `core/server.py`：仅启动核心 API 服务

### 常用命令
```powershell
# 安装依赖
pip install -r requirements.txt

# 启动全套
python start.py

# 仅跑核心服务
python core/server.py

# 全量测试
pytest -q
```

### 关键端口（见 `config.json`）
- Core API：`11450`
- 本地管理面板：`11451`
- 公网页面：`11452`

---

## 3. 请求鉴权与调用约定
### 鉴权
- 除 `/health`、`/api/health` 外，Core 默认要求请求头：`X-Internal-Token`
- 业务接口要求用户身份头：`X-Actor-User-Id`

### 用户 ID 规则
- 大多数 POST 需要 body 里 `user_id`
- `user_id` 必须与 `X-Actor-User-Id` 一致，否则拒绝

### 幂等与并发
- 多个关键写接口有幂等与防重表：`request_dedup`
- 战斗回合会话有持久化：`battle_sessions`

---

## 4. 目录速览（先看这些）
- `core/routes/`：所有 API 路由入口（按业务分模块）
- `core/services/`：业务主逻辑（结算、规则、风控、活动等）
- `core/game/`：静态定义与算法（怪物、道具、配方、掉落、战斗公式）
- `core/database/connection.py`：建表、索引、事务、常用 DB 接口
- `config.json`：主要配置中心（数值、开关、活动配置）
- `tests/`：回归与行为约束（改代码前后都应跑）

---

## 5. 功能地图（按模块）
### 账号与基础
- 注册/查用户：`core/routes/user.py`
- 状态查询、图鉴：`/api/stat/<user_id>`、`/api/codex/<user_id>`

### 修炼与突破
- 开始/结束修炼、状态、突破、签到：`core/routes/cultivation.py`

### 战斗
- 狩猎（自动 + 回合制）：`core/routes/combat.py`
- 秘境（自动 + 回合制）
- 战斗统一内核：`core/game/combat_kernel.py`
- 自动/回合共享公式，回合制支持 shadow 对账（用于一致性观测）

### 装备与强化
- 背包、穿脱、强化、分解、锻造：`core/routes/equipment.py`
- 锻造支持普通档 + 高投入档（`mode=high`）

### 技能
- 学习、装备、卸载、升级：`core/routes/skills.py`
- 主动技能参与战斗结算，支持熟练度成长

### 商店与道具
- 商店浏览、购买、用药：`core/routes/shop.py`
- 含铜币/金币双货币语义和轮换项

### 任务与成就
- 任务列表、单领、全领：`core/routes/quests.py`
- 成就列表、领取：`core/routes/achievements.py`

### PVP
- 对手推荐、挑战、记录、排名：`core/routes/pvp.py`
- 已有公平性护栏（战力窗口、友谊战等）

### 宗门与社交
- 宗门创建/加入/捐献/任务/战争/分舵：`core/routes/sect.py`
- 论道请求与处理：`core/routes/social.py`

### 经济扩展
- 炼丹：`core/routes/alchemy.py`
- 抽卡：`core/routes/gacha.py`
- 资源转化：`core/routes/resource_conversion.py`

### 活动与世界 Boss
- 活动列表/状态/领取/积分兑换：`core/routes/events.py`
- 世界 Boss 状态/攻击

---

## 6. 已实现的重点改造（近期）
### P2 已落地
- 1：战斗结算共享内核 + 双跑对账
- 2：秘境多步探索（节点化分支）
- 3：活动配置化 + 积分/兑换闭环
- 8：经济长线项
  - 炼丹成长（成功率/产出分随炼丹分提升）
  - 锻造高投入档
  - 掉落保底递增（`drop_pity`）
  - 境界曲线参数化（分段 growth + 秘境曲线配置）

### 明确未做


---

## 7. 关键配置（高频会改）
看 `config.json`：
- `balance.*`：数值主配置（狩猎、强化、锻造、炼丹、掉落等）
- `events.catalog`：活动定义（奖励、积分规则、兑换商店）
- `events.world_boss`：世界 Boss 配置
- `battle.kernel_shadow.*`：战斗双跑对账开关
- `battle.secret_realm_multi_step.*`：秘境多步探索开关
- `cooldowns.*`：各动作冷却

---

## 8. 数据库关键表（快速定位）
- `users`：玩家主状态
- `items`：背包物品
- `user_skills`：技能学习与装备
- `battle_logs`：战斗日志
- `user_quests` / `user_achievements`
- `sect_*`：宗门相关
- `pvp_records`
- `event_claims` / `event_points` / `event_point_logs` / `event_exchange_claims`
- `drop_pity`
- `request_dedup`：幂等防重
- `battle_sessions`：回合战会话

---

## 9. 给 AI 的最快阅读顺序
1. `config.json`（先掌握开关和数值）
2. `core/routes/__init__.py`（看总模块）
3. 目标业务对应 `core/routes/*.py`
4. 路由映射到 `core/services/*.py`
5. 公式/静态定义看 `core/game/*.py`
6. 数据一致性看 `core/database/connection.py`
7. 用例对照 `tests/`（这是“真实行为规范”）

---

## 10. 二次开发建议（避免踩坑）
- 写接口优先走 `services`，不要把复杂逻辑塞进 `routes`
- 涉及扣资源/发奖励必须走事务 `db_transaction()`
- 新增写接口尽量做幂等（复用 `request_dedup` 思路）
- 改数值先加配置项，不要硬编码
- 每次改动后跑 `pytest -q`

---

## 11. 当前健康状态
- 全量测试：`150 passed`
- 项目可直接本地启动、可继续迭代

