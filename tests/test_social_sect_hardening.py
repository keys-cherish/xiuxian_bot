from concurrent.futures import ThreadPoolExecutor

from flask import Flask

from core.database.connection import execute, fetch_one
from core.routes.pvp import pvp_challenge
from core.routes.sect import sect_create
from core.services import pvp_service, sect_service
from core.utils.timeutil import today_local
from tests.conftest import create_user


def _unwrap_route_result(resp):
    if isinstance(resp, tuple):
        response_obj, status_code = resp
        return int(status_code), response_obj.get_json() or {}
    return int(resp.status_code), resp.get_json() or {}


def _seed_basic_sect(sect_id: str = "S1", leader_id: str = "u1"):
    execute(
        """INSERT INTO sects
           (sect_id, name, description, leader_id, level, exp, fund_copper, fund_gold, max_members,
            war_wins, war_losses, last_war_time, created_at)
           VALUES (?, ?, ?, ?, 1, 0, 0, 0, 10, 0, 0, 0, 0)""",
        (sect_id, "测试宗门", "", leader_id),
    )
    execute(
        "INSERT INTO sect_members (sect_id, user_id, role, contribution, joined_at) VALUES (%s, %s, 'leader', 0, 0)",
        (sect_id, leader_id),
    )


def test_pvp_challenge_requires_actor_identity(test_db):
    create_user("u1", "甲", rank=5)
    create_user("u2", "乙", rank=5)

    app = Flask(__name__)
    with app.test_request_context(
        "/api/pvp/challenge",
        method="POST",
        json={"user_id": "u1", "opponent_id": "u2"},
    ):
        status, payload = _unwrap_route_result(pvp_challenge())
    assert status == 401
    assert payload.get("code") == "UNAUTHORIZED"


def test_sect_create_rejects_actor_mismatch(test_db):
    app = Flask(__name__)
    with app.test_request_context(
        "/api/sect/create",
        method="POST",
        json={"user_id": "u1", "name": "青云宗"},
        headers={"X-Actor-User-Id": "u2"},
    ):
        status, payload = _unwrap_route_result(sect_create())
    assert status == 403
    assert payload.get("code") == "FORBIDDEN"


def test_pvp_daily_limit_concurrent_single_success(test_db, monkeypatch):
    create_user("u1", "甲", rank=5, element="火")
    create_user("u2", "乙", rank=5, element="水")
    execute("UPDATE users SET stamina = 5, pvp_daily_count = 0, pvp_daily_reset = 0 WHERE user_id = %s", ("u1",))

    def fake_battle(challenger, defender, challenger_skills=None, defender_skills=None):
        return {
            "success": True,
            "winner_id": challenger["user_id"],
            "loser_id": defender["user_id"],
            "draw": False,
            "rounds": 1,
            "log": [],
            "message": "ok",
        }

    monkeypatch.setattr(pvp_service, "PVP_DAILY_LIMIT", 1)
    monkeypatch.setattr(pvp_service, "pvp_battle", fake_battle)
    monkeypatch.setattr(pvp_service.random, "randint", lambda a, b: a)

    def _challenge_once():
        return pvp_service.do_pvp_challenge("u1", "u2")

    with ThreadPoolExecutor(max_workers=2) as ex:
        results = list(ex.map(lambda _: _challenge_once(), range(2)))

    success_count = sum(1 for payload, status in results if status == 200 and payload.get("success"))
    fail_payloads = [payload for payload, status in results if not (status == 200 and payload.get("success"))]
    assert success_count == 1
    assert len(fail_payloads) == 1
    assert fail_payloads[0].get("code") == "LIMIT"

    pvp_row = fetch_one("SELECT pvp_daily_count FROM users WHERE user_id = %s", ("u1",))
    assert int(pvp_row["pvp_daily_count"]) == 1

    record_row = fetch_one("SELECT COUNT(1) AS c FROM pvp_records WHERE challenger_id = %s", ("u1",))
    assert int(record_row["c"]) == 1


def test_claim_quest_concurrent_single_reward(test_db):
    create_user("u1", "甲")
    _seed_basic_sect("S1", "u1")
    quest_id = execute(
        """INSERT INTO sect_quests
           (sect_id, quest_type, target, progress, reward_copper, reward_exp, assigned_date, completed, claimed)
           VALUES (?, 'donate', 10, 10, 123, 456, ?, 0, 0)""",
        ("S1", today_local()),
    )

    def _claim_once():
        return sect_service.claim_quest("u1", quest_id)

    with ThreadPoolExecutor(max_workers=2) as ex:
        results = list(ex.map(lambda _: _claim_once(), range(2)))

    success_count = sum(1 for payload, status in results if status == 200 and payload.get("success"))
    fail_codes = [payload.get("code") for payload, status in results if status != 200]
    assert success_count == 1
    assert len(fail_codes) == 1
    assert fail_codes[0] in {"CLAIMED", "NOT_DONE"}

    user = fetch_one("SELECT copper, exp FROM users WHERE user_id = %s", ("u1",))
    assert int(user["copper"]) == 1123
    assert int(user["exp"]) == 1456

    claim = fetch_one("SELECT claimed FROM sect_quest_claims WHERE quest_id = %s AND user_id = %s", (quest_id, "u1"))
    assert int(claim["claimed"]) == 1


def test_promote_and_kick_non_member_return_not_found(test_db):
    create_user("u1", "甲")
    create_user("u2", "乙")
    _seed_basic_sect("S1", "u1")

    promote_resp, promote_status = sect_service.promote_member("u1", "u2", "elder")
    assert promote_status == 404
    assert promote_resp.get("code") == "NOT_FOUND"

    kick_resp, kick_status = sect_service.kick_member("u1", "u2")
    assert kick_status == 404
    assert kick_resp.get("code") == "NOT_FOUND"
