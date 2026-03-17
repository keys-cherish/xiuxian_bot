import time

from flask import Flask

from core.database.connection import execute
from core.routes.skills import skills_list
from tests.conftest import create_user


def _unwrap(resp):
    if isinstance(resp, tuple):
        obj, status = resp
        return int(status), obj.get_json() or {}
    return int(resp.status_code), resp.get_json() or {}


def test_skills_list_unlockable_filters_by_user_element(test_db):
    create_user("u1", "甲", rank=10, element="土")
    app = Flask(__name__)

    with app.test_request_context(
        "/api/skills/u1",
        method="GET",
        headers={"X-Actor-User-Id": "u1"},
    ):
        status, payload = _unwrap(skills_list("u1"))

    assert status == 200
    unlockable = payload.get("unlockable", [])
    unlock_ids = {row.get("id") for row in unlockable}
    assert "stone_skin" in unlock_ids
    assert "earth_guard" in unlock_ids
    assert "earth_quake" in unlock_ids
    assert "fire_fury" not in unlock_ids
    assert "metal_pierce" not in unlock_ids
    assert all((not row.get("element")) or row.get("element") == "土" for row in unlockable)


def test_skills_list_without_element_hides_elemental_skills(test_db):
    execute(
        "INSERT INTO users (user_id, in_game_username, rank, element, created_at, exp, copper, gold) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        ("u2", "乙", 10, None, int(time.time()), 1000, 1000, 0),
    )
    app = Flask(__name__)

    with app.test_request_context(
        "/api/skills/u2",
        method="GET",
        headers={"X-Actor-User-Id": "u2"},
    ):
        status, payload = _unwrap(skills_list("u2"))

    assert status == 200
    unlockable = payload.get("unlockable", [])
    assert unlockable
    assert all(not row.get("element") for row in unlockable)
