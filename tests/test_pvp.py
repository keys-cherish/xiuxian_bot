from core.services import pvp_service
from core.database.connection import fetch_one, fetch_all
from tests.conftest import create_user


def test_calculate_elo_change():
    win, lose = pvp_service.calculate_elo_change(1000, 1000, k=32)
    assert win >= 5
    assert lose <= -5
    assert win + lose == 0 or win + lose in (-1, 1)


def test_pvp_challenge_updates(test_db, monkeypatch):
    create_user("u1", "甲", rank=5, element="火")
    create_user("u2", "乙", rank=5, element="水")

    def fake_battle(challenger, defender, challenger_skills=None, defender_skills=None):
        return {
            "success": True,
            "winner_id": challenger["user_id"],
            "loser_id": defender["user_id"],
            "draw": False,
            "rounds": 3,
            "log": [],
            "message": "ok",
        }

    monkeypatch.setattr(pvp_service, "pvp_battle", fake_battle)
    monkeypatch.setattr(pvp_service.random, "randint", lambda a, b: a)

    resp, status = pvp_service.do_pvp_challenge("u1", "u2", request_id="req-1")
    assert status == 200
    assert resp.get("success")
    assert resp.get("winner_id") == "u1"

    row = fetch_one("SELECT pvp_wins, pvp_losses, pvp_daily_count, pvp_rating FROM users WHERE user_id = %s", ("u1",))
    assert row["pvp_wins"] == 1
    assert row["pvp_losses"] == 0
    assert row["pvp_daily_count"] == 1
    assert row["pvp_rating"] >= 1000

    row2 = fetch_one("SELECT pvp_wins, pvp_losses, pvp_rating FROM users WHERE user_id = %s", ("u2",))
    assert row2["pvp_losses"] == 1

    logs = fetch_all("SELECT * FROM pvp_records WHERE challenger_id = %s", ("u1",))
    assert len(logs) == 1


def test_pvp_daily_limit(test_db, monkeypatch):
    create_user("u1", "甲", rank=5)
    create_user("u2", "乙", rank=5)

    from core.database.connection import execute
    execute(
        "UPDATE users SET pvp_daily_count = %s, pvp_daily_reset = %s WHERE user_id = %s",
        (pvp_service.PVP_DAILY_LIMIT, int(pvp_service.time.time()), "u1"),
    )

    def fake_battle(challenger, defender, challenger_skills=None, defender_skills=None):
        return {
            "success": True,
            "winner_id": challenger["user_id"],
            "loser_id": defender["user_id"],
            "draw": False,
            "rounds": 3,
            "log": [],
            "message": "ok",
        }

    monkeypatch.setattr(pvp_service, "pvp_battle", fake_battle)
    resp, status = pvp_service.do_pvp_challenge("u1", "u2")
    assert status == 400
    assert resp.get("code") == "LIMIT"


def test_pvp_recent_opponent_block(test_db, monkeypatch):
    create_user("u1", "甲", rank=5)
    create_user("u2", "乙", rank=5)
    now = int(pvp_service.time.time())

    from core.database.connection import execute
    execute(
        """INSERT INTO pvp_records
           (challenger_id, defender_id, winner_id, rounds,
            challenger_rating_before, defender_rating_before,
            challenger_rating_after, defender_rating_after,
            rewards_json, timestamp)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ("u1", "u2", "u1", 1, 1000, 1000, 1010, 990, "{}", now),
    )

    monkeypatch.setattr(pvp_service, "pvp_battle", lambda *args, **kwargs: {"winner_id": "u1", "loser_id": "u2", "draw": False, "rounds": 1, "log": []})

    resp, status = pvp_service.do_pvp_challenge("u1", "u2")
    assert status == 400
    assert resp.get("code") == "RECENT_OPPONENT"


def test_pvp_power_gap_friendly_mode(test_db, monkeypatch):
    create_user("u1", "甲", rank=8)
    create_user("u2", "乙", rank=1)

    from core.database.connection import execute
    execute(
        "UPDATE users SET attack = 1200, defense = 600, max_hp = 8000 WHERE user_id = %s",
        ("u1",),
    )
    execute(
        "UPDATE users SET attack = 5, defense = 2, max_hp = 80 WHERE user_id = %s",
        ("u2",),
    )

    monkeypatch.setattr(pvp_service, "pvp_battle", lambda *args, **kwargs: {"winner_id": "u1", "loser_id": "u2", "draw": False, "rounds": 1, "log": []})
    monkeypatch.setattr(pvp_service, "PVP_POWER_OUTSIDE_MODE", "friendly")

    resp, status = pvp_service.do_pvp_challenge("u1", "u2")
    assert status == 200
    assert resp.get("friendly") is True
    assert resp.get("rewards", {}).get("copper") == 0
    assert resp.get("rewards", {}).get("exp") == 0

    row = fetch_one("SELECT pvp_wins, pvp_losses FROM users WHERE user_id = %s", ("u1",))
    assert int(row["pvp_wins"]) == 0
