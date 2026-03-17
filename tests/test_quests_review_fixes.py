from concurrent.futures import ThreadPoolExecutor
import psycopg2.errors
import time
import datetime

from flask import Flask

from core.database.connection import execute, fetch_one
from core.game.leaderboards import get_stage_goal
from core.game.quests import get_all_quest_defs
from core.game.secret_realms import get_secret_realm_by_id
from core.game.signin import get_signin_reward
from core.routes.misc import misc_bp, leaderboard
from core.services import achievements_service
from core.services import settlement as settlement_service
from core.services import turn_battle_service as tbs
from core.services.quests_service import ensure_daily_quests, today_str
from core.services.settlement import settle_hunt, settle_secret_realm_explore
from core.services.settlement_extra import settle_signin
from tests.conftest import create_user


def _unwrap_route_result(resp):
    if isinstance(resp, tuple):
        response_obj, status_code = resp
        return int(status_code), response_obj.get_json() or {}
    return int(resp.status_code), resp.get_json() or {}


def test_settle_hunt_victory_increments_daily_hunt(monkeypatch, test_db):
    create_user("u1", "甲", rank=5)
    calls = []

    monkeypatch.setattr(
        settlement_service,
        "hunt_monster",
        lambda user, monster_id, learned_skills, **kwargs: {
            "success": True,
            "victory": True,
            "monster": {"id": monster_id, "name": "野猪"},
            "attacker_remaining_hp": 90,
            "attacker_remaining_mp": 40,
            "rewards": {"exp": 0, "copper": 0, "gold": 0},
            "rounds": 1,
            "log": [],
            "message": "ok",
        },
    )
    monkeypatch.setattr(settlement_service, "calculate_drop_rewards", lambda *args, **kwargs: [])
    monkeypatch.setattr(settlement_service, "increment_quest", lambda user_id, quest_id, amount=1, day=None: calls.append((user_id, quest_id, amount)))

    payload, status = settle_hunt(
        user_id="u1",
        monster_id="wild_boar",
        request_id=None,
        hunt_cooldown_seconds=0,
        now=int(time.time()),
    )
    assert status == 200
    assert payload.get("victory") is True
    assert calls == [("u1", "daily_hunt", 1)]


def test_turn_finalize_hunt_victory_increments_daily_hunt(monkeypatch, test_db):
    create_user("u1", "甲", rank=5)
    calls = []

    monkeypatch.setattr(tbs, "increment_quest", lambda user_id, quest_id, amount=1, day=None: calls.append((user_id, quest_id, amount)))
    monkeypatch.setattr(tbs, "calculate_drop_rewards", lambda *args, **kwargs: [])
    monkeypatch.setattr(tbs, "ensure_monster", lambda *args, **kwargs: None)
    monkeypatch.setattr(tbs, "ensure_item", lambda *args, **kwargs: None)
    monkeypatch.setattr(tbs, "random", type("R", (), {"random": staticmethod(lambda: 1.0)})())

    session = {
        "user_id": "u1",
        "monster": {"id": "wild_boar", "name": "野猪"},
        "user_snapshot": fetch_one("SELECT * FROM users WHERE user_id = %s", ("u1",)),
        "player": {"hp": 80, "mp": 30},
        "round": 2,
        "history": [],
        "hunt_index": 1,
    }
    payload = tbs._finalize_hunt(session, True)
    assert payload.get("victory") is True
    assert calls == [("u1", "daily_hunt", 1)]


def test_settle_secret_realm_explore_increments_daily_secret_realm(monkeypatch, test_db):
    create_user("u1", "甲", rank=5)
    calls = []

    monkeypatch.setattr(
        settlement_service,
        "roll_secret_realm_encounter",
        lambda realm, path="normal": {"type": "none", "label": "空境"},
    )
    monkeypatch.setattr(
        settlement_service,
        "roll_secret_realm_rewards",
        lambda *args, **kwargs: {"event": "平安归来", "exp": 20, "copper": 10, "gold": 0, "drop_item_ids": []},
    )
    monkeypatch.setattr(settlement_service, "increment_quest", lambda user_id, quest_id, amount=1, day=None: calls.append((user_id, quest_id, amount)))

    payload, status = settle_secret_realm_explore(
        user_id="u1",
        realm_id="mist_forest",
        path="normal",
        request_id=None,
        secret_cooldown_seconds=0,
        now=int(time.time()),
    )
    assert status == 200
    assert payload.get("success") is True
    assert calls == [("u1", "daily_secret_realm", 1)]


def test_turn_finalize_secret_no_battle_increments_daily_secret_realm(monkeypatch, test_db):
    create_user("u1", "甲", rank=5)
    calls = []

    monkeypatch.setattr(
        tbs,
        "roll_secret_realm_rewards",
        lambda *args, **kwargs: {"event": "平安归来", "exp": 20, "copper": 10, "gold": 0, "drop_item_ids": []},
    )
    monkeypatch.setattr(tbs, "increment_quest", lambda user_id, quest_id, amount=1, day=None: calls.append((user_id, quest_id, amount)))
    monkeypatch.setattr(tbs, "ensure_item", lambda *args, **kwargs: None)

    user = fetch_one("SELECT * FROM users WHERE user_id = %s", ("u1",))
    realm = get_secret_realm_by_id("mist_forest")
    payload = tbs._finalize_secret_no_battle(
        "u1",
        user,
        realm,
        "normal",
        int(time.time()),
        encounter={"type": "none", "label": "空境"},
    )
    assert payload.get("success") is True
    assert calls == [("u1", "daily_secret_realm", 1)]


def test_turn_finalize_secret_battle_increments_daily_secret_realm(monkeypatch, test_db):
    create_user("u1", "甲", rank=5)
    calls = []

    monkeypatch.setattr(
        tbs,
        "roll_secret_realm_rewards",
        lambda *args, **kwargs: {"event": "鏖战归来", "exp": 20, "copper": 10, "gold": 0, "drop_item_ids": []},
    )
    monkeypatch.setattr(tbs, "increment_quest", lambda user_id, quest_id, amount=1, day=None: calls.append((user_id, quest_id, amount)))
    monkeypatch.setattr(tbs, "ensure_item", lambda *args, **kwargs: None)

    session = {
        "user_id": "u1",
        "user_snapshot": fetch_one("SELECT * FROM users WHERE user_id = %s", ("u1",)),
        "realm": get_secret_realm_by_id("mist_forest"),
        "path": "normal",
        "player": {"hp": 1, "mp": 10},
        "encounter": {"type": "monster", "label": "野怪"},
        "monster": {"id": "wild_boar", "name": "野猪"},
        "history": [],
    }
    payload = tbs._finalize_secret(session, False)
    assert payload.get("success") is True
    assert calls == [("u1", "daily_secret_realm", 1)]


def test_settle_signin_concurrent_single_reward(test_db):
    create_user("u1", "甲", rank=1)

    def _signin_once():
        return settle_signin(user_id="u1")

    with ThreadPoolExecutor(max_workers=4) as ex:
        results = list(ex.map(lambda _: _signin_once(), range(4)))

    success_payloads = [payload for payload, status in results if status == 200 and payload.get("success")]
    assert len(success_payloads) == 4
    reward_payloads = [p for p in success_payloads if not p.get("already_signed")]
    assert len(reward_payloads) == 1

    reward = get_signin_reward(1, user_rank=1)
    user = fetch_one(
        "SELECT copper, exp, gold, consecutive_sign_days, max_signin_days FROM users WHERE user_id = %s",
        ("u1",),
    )
    assert int(user["copper"]) == 1000 + int(reward.get("copper", 0) or 0)
    assert int(user["exp"]) == 1000 + int(reward.get("exp", 0) or 0)
    assert int(user["gold"]) == int(reward.get("gold", 0) or 0)
    assert int(user["consecutive_sign_days"]) == 1
    assert int(user["max_signin_days"]) == 1

    today = today_str()
    quest = fetch_one(
        "SELECT progress FROM user_quests WHERE user_id = %s AND quest_id = %s AND assigned_date = %s",
        ("u1", "daily_signin", today),
    )
    assert quest is not None
    assert int(quest["progress"]) == 1


def test_signin_month_milestone_bonus(test_db):
    create_user("u1", "甲", rank=1)
    tz = datetime.timezone(datetime.timedelta(hours=8))
    month_key = datetime.datetime.now(tz=tz).strftime("%Y-%m")

    execute(
        "UPDATE users SET signin_month_key = %s, signin_month_days = %s, signin_month_claim_bits = %s, last_sign_timestamp = 0 WHERE user_id = %s",
        (month_key, 6, 0, "u1"),
    )

    payload, status = settle_signin(user_id="u1")
    assert status == 200
    rewards = payload.get("rewards", {}) or {}
    month_bonus = rewards.get("month_bonus") or {}
    assert rewards.get("month_days") == 7
    assert month_bonus.get("copper", 0) > 0

    daily = get_signin_reward(1, user_rank=1)
    user = fetch_one("SELECT copper, exp, gold FROM users WHERE user_id = %s", ("u1",))
    assert int(user["copper"]) == 1000 + int(daily.get("copper", 0) or 0) + int(month_bonus.get("copper", 0) or 0)
    assert int(user["exp"]) == 1000 + int(daily.get("exp", 0) or 0) + int(month_bonus.get("exp", 0) or 0)

    herb_row = fetch_one("SELECT SUM(quantity) AS q FROM items WHERE user_id = %s AND item_id = %s", ("u1", "herb"))
    assert int(herb_row["q"] or 0) >= 5


def test_settle_quest_claim_all_claims_completed(test_db):
    create_user("u1", "甲", rank=1)
    today = today_str()
    ensure_daily_quests("u1", today)

    defs = get_all_quest_defs()
    q1 = defs[0]["id"]
    q2 = defs[1]["id"]
    execute(
        "UPDATE user_quests SET progress = goal, claimed = 0 WHERE user_id = %s AND quest_id IN (%s, %s) AND assigned_date = %s",
        ("u1", q1, q2, today),
    )

    resp, status = settlement_service.settle_quest_claim_all(
        user_id="u1",
        request_id=None,
        claim_cooldown_seconds=0,
        today=today,
        now=int(time.time()),
    )
    assert status == 200
    assert resp.get("claimed_count") == 2

    scale = settlement_service.APP_CONFIG.get("balance", {}).get("quest_reward_scale", {}) or {}
    sc_c = float(scale.get("copper", 1.0))
    sc_e = float(scale.get("exp", 1.0))
    sc_g = float(scale.get("gold", 1.0))
    qdef_map = {q["id"]: q for q in defs}
    expected_copper = int(round(qdef_map[q1]["rewards"]["copper"] * sc_c)) + int(round(qdef_map[q2]["rewards"]["copper"] * sc_c))
    expected_exp = int(round(qdef_map[q1]["rewards"]["exp"] * sc_e)) + int(round(qdef_map[q2]["rewards"]["exp"] * sc_e))
    expected_gold = int(round(qdef_map[q1]["rewards"].get("gold", 0) * sc_g)) + int(round(qdef_map[q2]["rewards"].get("gold", 0) * sc_g))
    assert resp.get("rewards", {}).get("copper") == expected_copper
    assert resp.get("rewards", {}).get("exp") == expected_exp
    assert resp.get("rewards", {}).get("gold") == expected_gold

    rows = fetch_one(
        "SELECT COUNT(1) AS c FROM user_quests WHERE user_id = %s AND assigned_date = %s AND claimed = 1 AND quest_id IN (%s, %s)",
        ("u1", today, q1, q2),
    )
    assert int(rows["c"]) == 2


def test_ensure_daily_quests_backfills_missing_rows_without_resetting_progress(test_db):
    create_user("u1", "甲", rank=1)
    day = today_str()

    execute(
        "INSERT INTO user_quests (user_id, quest_id, progress, goal, claimed, assigned_date) VALUES (%s, %s, %s, %s, 0, %s)",
        ("u1", "daily_signin", 1, 1, day),
    )

    ensure_daily_quests("u1", day)

    total = fetch_one(
        "SELECT COUNT(1) AS c FROM user_quests WHERE user_id = %s AND assigned_date = %s",
        ("u1", day),
    )
    assert int(total["c"]) == len(get_all_quest_defs())

    signin = fetch_one(
        "SELECT progress FROM user_quests WHERE user_id = %s AND quest_id = %s AND assigned_date = %s",
        ("u1", "daily_signin", day),
    )
    assert int(signin["progress"]) == 1


def test_ensure_daily_quests_concurrent_no_duplicate_rows(test_db):
    create_user("u1", "甲", rank=1)
    day = today_str()

    with ThreadPoolExecutor(max_workers=4) as ex:
        list(ex.map(lambda _: ensure_daily_quests("u1", day), range(4)))

    row = fetch_one(
        "SELECT COUNT(1) AS c FROM user_quests WHERE user_id = %s AND assigned_date = %s",
        ("u1", day),
    )
    assert int(row["c"]) == len(get_all_quest_defs())


def test_user_quests_unique_index_rejects_duplicate_day_rows(test_db):
    create_user("u1", "甲", rank=1)
    day = today_str()
    execute(
        "INSERT INTO user_quests (user_id, quest_id, progress, goal, claimed, assigned_date) VALUES (%s, %s, %s, %s, 0, %s)",
        ("u1", "daily_signin", 0, 1, day),
    )
    try:
        execute(
            "INSERT INTO user_quests (user_id, quest_id, progress, goal, claimed, assigned_date) VALUES (%s, %s, %s, %s, 0, %s)",
            ("u1", "daily_signin", 0, 1, day),
        )
        raise AssertionError("expected psycopg2.errors.UniqueViolation")
    except psycopg2.errors.UniqueViolation:
        pass


def test_signin_streak_achievement_uses_historical_max_streak(test_db):
    create_user("u1", "甲", rank=1)
    execute(
        "UPDATE users SET consecutive_sign_days = 1, max_signin_days = 7 WHERE user_id = %s",
        ("u1",),
    )

    payload, status = achievements_service.get_achievements("u1")
    assert status == 200
    signin_ach = next(a for a in payload["achievements"] if a["id"] == "signin_7")
    assert int(signin_ach["progress"]) == 7
    assert signin_ach["completed"] is True


def test_leaderboard_exp_growth_alias_maps_to_total_exp_mode(test_db):
    create_user("u1", "甲", rank=2)
    create_user("u2", "乙", rank=1)
    execute("UPDATE users SET exp = %s WHERE user_id = %s", (1200, "u1"))
    execute("UPDATE users SET exp = %s WHERE user_id = %s", (3000, "u2"))

    app = Flask(__name__)
    app.register_blueprint(misc_bp)
    with app.test_request_context("/api/leaderboard?mode=exp_growth"):
        status, payload = _unwrap_route_result(leaderboard())
    assert status == 200
    assert payload.get("mode") == "exp"
    assert payload["entries"][0]["user_id"] == "u1"


def test_stage_goal_low_rank_uses_total_exp_label():
    stage_goal = get_stage_goal(5)
    assert stage_goal.get("recommended_mode") == "exp"
    assert stage_goal.get("goal_label") == "修为总量榜"


def test_event_status_includes_timing_fields(test_db):
    create_user("u1", "甲")
    from core.services.events_service import get_event_status

    payload = get_event_status("u1")
    assert payload.get("success") is True
    assert payload.get("events")
    event = payload["events"][0]
    assert "end_ts" in event
    assert "remaining_days" in event
    assert "next_refresh_ts" in event
