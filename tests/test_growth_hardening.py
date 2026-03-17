from concurrent.futures import ThreadPoolExecutor

import pytest
from flask import Flask

from core.database.connection import fetch_one
from tests.conftest import create_user

TEST_INTERNAL_TOKEN = "unit-test-internal-token"


@pytest.fixture()
def internal_token_env(test_db, monkeypatch):
    monkeypatch.setenv("XXBOT_INTERNAL_API_TOKEN", TEST_INTERNAL_TOKEN)
    from core.config import config
    config.reload()
    yield

    monkeypatch.delenv("XXBOT_INTERNAL_API_TOKEN", raising=False)
    config.reload()


def test_internal_token_validation(internal_token_env):
    from core.server import is_internal_request_authorized

    assert is_internal_request_authorized("") is False
    assert is_internal_request_authorized("wrong-token") is False
    assert is_internal_request_authorized(TEST_INTERNAL_TOKEN) is True


def test_skill_learn_concurrent_single_success(test_db):
    from core.routes.skills import skill_learn

    create_user("u1", "甲", rank=5)
    app = Flask(__name__)

    def _learn_once():
        with app.test_request_context(
            "/api/skills/learn",
            method="POST",
            json={"user_id": "u1", "skill_id": "stone_skin"},
            headers={"X-Actor-User-Id": "u1"},
        ):
            resp = skill_learn()
            if isinstance(resp, tuple):
                response_obj, status = resp
                return status, response_obj.get_json() or {}
            return resp.status_code, resp.get_json() or {}

    with ThreadPoolExecutor(max_workers=4) as ex:
        results = list(ex.map(lambda _: _learn_once(), range(4)))

    success_count = sum(1 for status, payload in results if status == 200 and payload.get("success"))
    assert success_count == 1

    user = fetch_one("SELECT copper FROM users WHERE user_id = %s", ("u1",))
    assert int(user["copper"]) == 600

    row = fetch_one(
        "SELECT COUNT(1) AS c FROM user_skills WHERE user_id = %s AND skill_id = %s",
        ("u1", "stone_skin"),
    )
    assert int(row["c"]) == 1


def test_achievement_claim_concurrent_single_reward(test_db):
    from core.services.achievements_service import claim_achievement

    create_user("u1", "甲", rank=7)

    with ThreadPoolExecutor(max_workers=5) as ex:
        results = list(ex.map(lambda _: claim_achievement("u1", "rank_7"), range(5)))

    success_count = sum(1 for payload, status in results if status == 200 and payload.get("success"))
    assert success_count == 5

    user = fetch_one("SELECT copper, exp FROM users WHERE user_id = %s", ("u1",))
    assert int(user["copper"]) == 1300
    assert int(user["exp"]) == 1200

    row = fetch_one(
        "SELECT COUNT(1) AS c FROM user_achievements WHERE user_id = %s AND achievement_id = %s AND claimed = 1",
        ("u1", "rank_7"),
    )
    assert int(row["c"]) == 1


def test_event_claim_concurrent_single_reward(test_db):
    from core.services.events_service import claim_event_reward

    create_user("u1", "甲", rank=7)

    with ThreadPoolExecutor(max_workers=5) as ex:
        results = list(ex.map(lambda _: claim_event_reward("u1", "spring_festival"), range(5)))

    success_count = sum(1 for payload, status in results if status == 200 and payload.get("success"))
    assert success_count == 1

    user = fetch_one("SELECT copper, exp FROM users WHERE user_id = %s", ("u1",))
    assert int(user["copper"]) == 1320
    assert int(user["exp"]) == 1150

    row = fetch_one(
        "SELECT claims FROM event_claims WHERE user_id = %s AND event_id = %s",
        ("u1", "spring_festival"),
    )
    assert row is not None
    assert int(row["claims"]) == 1
