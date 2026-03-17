import time

from flask import Flask

from core.database.connection import execute, fetch_one
from core.routes.events import (
    events_list,
    events_status,
    events_claim,
    events_exchange,
    worldboss_status,
    worldboss_attack,
)
from core.routes.gacha import gacha_status as gacha_status_route, gacha_pity, gacha_pull as gacha_pull_route
from core.routes.pvp import (
    pvp_ranking,
    pvp_records,
    pvp_opponents,
    pvp_challenge,
)
from tests.conftest import create_user


def _unwrap(resp):
    if isinstance(resp, tuple):
        obj, status = resp
        return int(status), obj.get_json() or {}
    return int(resp.status_code), resp.get_json() or {}


def test_events_claim_exchange_and_worldboss_routes(test_db):
    create_user("u1", "甲", rank=12)
    now = int(time.time())
    execute(
        "UPDATE users SET stamina = 24, stamina_updated_at = %s WHERE user_id = %s",
        (now, "u1"),
    )
    app = Flask(__name__)

    with app.test_request_context("/api/events", method="GET"):
        list_status, list_payload = _unwrap(events_list())
    assert list_status == 200
    assert list_payload.get("success") is True
    active_events = list_payload.get("events") or []
    assert active_events
    chosen_event = next((e for e in active_events if e.get("exchange_shop")), active_events[0])
    event_id = str(chosen_event.get("id"))
    exchange = (chosen_event.get("exchange_shop") or [None])[0]
    assert exchange is not None
    exchange_id = str(exchange.get("id"))
    cost_points = int(exchange.get("cost_points", 0) or 0)

    with app.test_request_context(
        f"/api/events/status/u1",
        method="GET",
        headers={"X-Actor-User-Id": "u1"},
    ):
        before_status, before_payload = _unwrap(events_status("u1"))
    assert before_status == 200
    before_event = next((e for e in (before_payload.get("events") or []) if str(e.get("id")) == event_id), None)
    assert before_event is not None

    with app.test_request_context(
        "/api/events/claim",
        method="POST",
        json={"user_id": "u1", "event_id": event_id},
        headers={"X-Actor-User-Id": "u1"},
    ):
        claim_status, claim_payload = _unwrap(events_claim())
    assert claim_status == 200
    assert claim_payload.get("success") is True

    # 补足积分，确保兑换分支可稳定通过
    execute(
        """
        INSERT INTO event_points(user_id, event_id, points_total, points_spent, updated_at)
        VALUES (?, ?, ?, 0, ?)
        ON CONFLICT(user_id, event_id)
        DO UPDATE SET points_total = excluded.points_total, updated_at = excluded.updated_at
        """,
        ("u1", event_id, max(999, cost_points + 50), int(time.time())),
    )

    with app.test_request_context(
        "/api/events/exchange",
        method="POST",
        json={"user_id": "u1", "event_id": event_id, "exchange_id": exchange_id, "quantity": 1},
        headers={"X-Actor-User-Id": "u1"},
    ):
        ex_status, ex_payload = _unwrap(events_exchange())
    assert ex_status == 200
    assert ex_payload.get("success") is True
    assert int(ex_payload.get("cost_points", 0) or 0) == cost_points
    assert int(ex_payload.get("points_balance", 0) or 0) >= 0

    point_row = fetch_one(
        "SELECT points_total, points_spent FROM event_points WHERE user_id = %s AND event_id = %s",
        ("u1", event_id),
    )
    assert point_row is not None
    assert int(point_row["points_spent"] or 0) >= cost_points

    with app.test_request_context("/api/worldboss/status", method="GET"):
        wb_status_before, wb_payload_before = _unwrap(worldboss_status())
    assert wb_status_before == 200
    boss_before = (wb_payload_before.get("boss") or {})
    hp_before = int(boss_before.get("hp", 0) or 0)
    assert hp_before > 0

    with app.test_request_context(
        "/api/worldboss/attack",
        method="POST",
        json={"user_id": "u1"},
        headers={"X-Actor-User-Id": "u1"},
    ):
        atk_status, atk_payload = _unwrap(worldboss_attack())
    assert atk_status == 200
    assert atk_payload.get("success") is True
    assert int(atk_payload.get("attacks_left", 0) or 0) == 4
    assert int(atk_payload.get("boss_hp", 0) or 0) < hp_before


def test_gacha_status_pull_and_pity_routes(test_db):
    create_user("u1", "甲", rank=10)
    now = int(time.time())
    execute(
        """
        UPDATE users
        SET gold = 100, stamina = 24, stamina_updated_at = ?,
            gacha_free_today = 0, gacha_paid_today = 0, gacha_daily_reset = ?
        WHERE user_id = ?
        """,
        (now, now, "u1"),
    )
    app = Flask(__name__)

    with app.test_request_context(
        "/api/gacha/status/u1",
        method="GET",
        headers={"X-Actor-User-Id": "u1"},
    ):
        st_status, st_payload = _unwrap(gacha_status_route("u1"))
    assert st_status == 200
    assert st_payload.get("success") is True
    assert int((st_payload.get("status") or {}).get("free_remaining", -1)) == 3
    assert int((st_payload.get("status") or {}).get("paid_remaining", -1)) == 15

    with app.test_request_context(
        "/api/gacha/pity/u1%sbanner_id=100001",
        method="GET",
        headers={"X-Actor-User-Id": "u1"},
    ):
        pity_before_status, pity_before_payload = _unwrap(gacha_pity("u1"))
    assert pity_before_status == 200
    assert pity_before_payload.get("success") is True
    assert int((pity_before_payload.get("pity") or {}).get("total_pulls", 0) or 0) == 0

    with app.test_request_context(
        "/api/gacha/pull",
        method="POST",
        json={"user_id": "u1", "banner_id": 100001, "count": 1, "force_paid": True},
        headers={"X-Actor-User-Id": "u1"},
    ):
        pull_status, pull_payload = _unwrap(gacha_pull_route())
    assert pull_status == 200
    assert pull_payload.get("success") is True
    assert pull_payload.get("results")
    assert int((pull_payload.get("cost") or {}).get("amount", 0) or 0) == 1
    assert int(pull_payload.get("stamina_cost", 0) or 0) == 1

    with app.test_request_context(
        "/api/gacha/pity/u1%sbanner_id=100001",
        method="GET",
        headers={"X-Actor-User-Id": "u1"},
    ):
        pity_after_status, pity_after_payload = _unwrap(gacha_pity("u1"))
    assert pity_after_status == 200
    assert int((pity_after_payload.get("pity") or {}).get("total_pulls", 0) or 0) == 1

    user_row = fetch_one("SELECT gold, stamina FROM users WHERE user_id = %s", ("u1",))
    assert user_row is not None
    assert int(user_row["gold"] or 0) == 99
    assert float(user_row["stamina"] or 0) <= 23.0


def test_pvp_ranking_records_opponents_and_challenge_route(test_db, monkeypatch):
    create_user("u1", "甲", rank=8)
    create_user("u2", "乙", rank=8)
    create_user("u3", "丙", rank=8)
    execute("UPDATE users SET pvp_rating = 1300, pvp_wins = 5 WHERE user_id = 'u2'")
    execute("UPDATE users SET pvp_rating = 1200, pvp_wins = 3 WHERE user_id = 'u1'")
    execute("UPDATE users SET pvp_rating = 1100, pvp_wins = 1 WHERE user_id = 'u3'")
    execute(
        """INSERT INTO pvp_records
           (challenger_id, defender_id, winner_id, rounds,
            challenger_rating_before, defender_rating_before,
            challenger_rating_after, defender_rating_after, rewards_json, timestamp)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ("u1", "u2", "u1", 3, 1200, 1300, 1212, 1288, '{"copper":120,"exp":80}', int(time.time())),
    )
    app = Flask(__name__)

    with app.test_request_context("/api/pvp/ranking?limit=3", method="GET"):
        rk_status, rk_payload = _unwrap(pvp_ranking())
    assert rk_status == 200
    assert rk_payload.get("success") is True
    entries = rk_payload.get("entries") or []
    assert len(entries) >= 3
    assert entries[0].get("user_id") == "u2"
    assert int(entries[0].get("pvp_rating", 0) or 0) >= int(entries[1].get("pvp_rating", 0) or 0)

    with app.test_request_context(
        "/api/pvp/records/u1%slimit=5",
        method="GET",
        headers={"X-Actor-User-Id": "u1"},
    ):
        rec_status, rec_payload = _unwrap(pvp_records("u1"))
    assert rec_status == 200
    assert rec_payload.get("success") is True
    records = rec_payload.get("records") or []
    assert records
    assert isinstance((records[0].get("rewards") or {}), dict)

    with app.test_request_context(
        "/api/pvp/opponents/u1%slimit=2",
        method="GET",
        headers={"X-Actor-User-Id": "u1"},
    ):
        op_status, op_payload = _unwrap(pvp_opponents("u1"))
    assert op_status == 200
    assert op_payload.get("success") is True
    assert len(op_payload.get("opponents") or []) <= 2

    captured = {}

    def _fake_challenge(user_id, opponent_id, request_id=None):
        captured["user_id"] = user_id
        captured["opponent_id"] = opponent_id
        captured["request_id"] = request_id
        return {"success": True, "winner_id": user_id, "opponent_id": opponent_id}, 200

    monkeypatch.setattr("core.routes.pvp.do_pvp_challenge", _fake_challenge)
    with app.test_request_context(
        "/api/pvp/challenge",
        method="POST",
        json={"user_id": "u1", "opponent_id": "u2", "request_id": "RID-PVP-1"},
        headers={"X-Actor-User-Id": "u1"},
    ):
        ch_status, ch_payload = _unwrap(pvp_challenge())
    assert ch_status == 200
    assert ch_payload.get("success") is True
    assert captured.get("user_id") == "u1"
    assert captured.get("opponent_id") == "u2"
    assert captured.get("request_id") == "RID-PVP-1"
