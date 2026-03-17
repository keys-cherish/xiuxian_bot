"""quests / achievements 路由集成测试：权限、缺参、成功路径、幂等领取。"""

import pytest
from flask import Flask

from core.routes.achievements import achievements_bp, achievements_list, achievements_claim
from core.routes.quests import quests_bp, quests_list, quest_claim
from core.services import achievements_service
from core.services import quests_service
from core.database.connection import execute
from tests.conftest import create_user


# ─── helpers ────────────────────────────────────────────────────────────────

def _unwrap(resp):
    if isinstance(resp, tuple):
        obj, status = resp
        return int(status), obj.get_json() or {}
    return int(resp.status_code), resp.get_json() or {}


def _req(path, method="POST", json=None, headers=None):
    app = Flask(__name__)
    app.register_blueprint(achievements_bp)
    app.register_blueprint(quests_bp)
    kwargs = {"method": method}
    if json is not None:
        kwargs["json"] = json
    if headers:
        kwargs["headers"] = headers
    return app.test_request_context(path, **kwargs)


# ─── achievements ────────────────────────────────────────────────────────────

def test_achievements_list_auth_mismatch(test_db):
    """path user_id 与 actor 不符返回 403。"""
    create_user("u1", "甲")
    create_user("u2", "乙")
    with _req("/api/achievements/u1", method="GET",
              headers={"X-Actor-User-Id": "u2"}):
        status, payload = _unwrap(achievements_list("u1"))
    assert status == 403
    assert payload["code"] == "FORBIDDEN"


def test_achievements_list_ok(test_db, monkeypatch):
    """正常用户返回成就列表。"""
    create_user("u1", "甲")

    monkeypatch.setattr(
        achievements_service, "get_achievements",
        lambda uid: ({"success": True, "achievements": []}, 200)
    )
    with _req("/api/achievements/u1", method="GET",
              headers={"X-Actor-User-Id": "u1"}):
        status, payload = _unwrap(achievements_list("u1"))
    assert status == 200
    assert "achievements" in payload


def test_achievements_claim_requires_actor(test_db):
    """无 actor header 返回 401。"""
    create_user("u1", "甲")
    with _req("/api/achievements/claim",
              json={"user_id": "u1", "achievement_id": "first_hunt"}):
        status, payload = _unwrap(achievements_claim())
    assert status == 401


def test_achievements_claim_missing_achievement_id(test_db):
    create_user("u1", "甲")
    with _req("/api/achievements/claim",
              json={"user_id": "u1"},
              headers={"X-Actor-User-Id": "u1"}):
        status, payload = _unwrap(achievements_claim())
    assert status == 400
    assert payload["code"] == "MISSING_PARAMS"


def test_achievements_claim_ok(test_db, monkeypatch):
    create_user("u1", "甲")
    import core.routes.achievements as ach_routes
    monkeypatch.setattr(
        ach_routes, "claim_achievement",
        lambda uid, aid: ({"success": True, "reward": {}}, 200)
    )
    with _req("/api/achievements/claim",
              json={"user_id": "u1", "achievement_id": "first_hunt"},
              headers={"X-Actor-User-Id": "u1"}):
        status, payload = _unwrap(achievements_claim())
    assert status == 200
    assert payload["success"] is True


def test_achievement_claim_idempotent(test_db):
    create_user("u1", "甲", rank=7)
    resp1, status1 = achievements_service.claim_achievement("u1", "rank_7")
    assert status1 == 200
    assert resp1.get("success") is True

    resp2, status2 = achievements_service.claim_achievement("u1", "rank_7")
    assert status2 == 200
    assert resp2.get("already_claimed") is True


# ─── quests list ─────────────────────────────────────────────────────────────

def test_quests_list_user_not_found(test_db):
    with _req("/api/quests/ghost", method="GET",
              headers={"X-Actor-User-Id": "ghost"}):
        status, payload = _unwrap(quests_list("ghost"))
    assert status == 404


def test_quests_list_ok(test_db):
    create_user("u1", "甲")
    with _req("/api/quests/u1", method="GET",
              headers={"X-Actor-User-Id": "u1"}):
        status, payload = _unwrap(quests_list("u1"))
    assert status == 200
    assert "quests" in payload


# ─── quest claim ─────────────────────────────────────────────────────────────

def test_quest_claim_requires_actor(test_db):
    create_user("u1", "甲")
    with _req("/api/quests/claim",
              json={"user_id": "u1", "quest_id": "hunt_5"}):
        status, payload = _unwrap(quest_claim())
    assert status == 401


def test_quest_claim_missing_quest_id(test_db):
    create_user("u1", "甲")
    with _req("/api/quests/claim",
              json={"user_id": "u1"},
              headers={"X-Actor-User-Id": "u1"}):
        status, payload = _unwrap(quest_claim())
    assert status == 400
    assert payload["code"] == "MISSING_PARAMS"


