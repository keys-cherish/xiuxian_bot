"""combat 路由集成测试：权限校验、缺参、回合制链路（start/action/status）。"""

import pytest
from flask import Flask

from core.routes.combat import (
    combat_bp,
    hunt,
    hunt_status,
    hunt_turn_start,
    hunt_turn_action,
)
from core.services import turn_battle_service
from tests.conftest import create_user


# ─── helpers ────────────────────────────────────────────────────────────────

def _unwrap(resp):
    if isinstance(resp, tuple):
        obj, status = resp
        return int(status), obj.get_json() or {}
    return int(resp.status_code), resp.get_json() or {}


def _req(path, method="POST", json=None, headers=None, args=None):
    """构建 Flask test_request_context。"""
    app = Flask(__name__)
    app.register_blueprint(combat_bp)
    kwargs = {"method": method}
    if json is not None:
        kwargs["json"] = json
    if headers:
        kwargs["headers"] = headers
    if args:
        kwargs["query_string"] = args
    return app.test_request_context(path, **kwargs)


# ─── /api/hunt ───────────────────────────────────────────────────────────────

def test_hunt_requires_actor(test_db):
    """无 X-Actor-User-Id 时返回 401。"""
    create_user("u1", "甲")
    with _req("/api/hunt", json={"user_id": "u1", "monster_id": "slime"}):
        status, payload = _unwrap(hunt())
    assert status == 401
    assert payload["code"] == "UNAUTHORIZED"


def test_hunt_missing_monster_id(test_db):
    """缺少 monster_id 返回 400。"""
    create_user("u1", "甲")
    with _req("/api/hunt",
              json={"user_id": "u1"},
              headers={"X-Actor-User-Id": "u1"}):
        status, payload = _unwrap(hunt())
    assert status == 400
    assert payload["code"] == "MISSING_PARAMS"


# ─── /api/hunt/status/<user_id> ──────────────────────────────────────────────

def test_hunt_status_user_not_found(test_db):
    """查询不存在用户的冷却状态返回 404。"""
    with _req("/api/hunt/status/ghost", method="GET",
              headers={"X-Actor-User-Id": "ghost"}):
        status, payload = _unwrap(hunt_status("ghost"))
    assert status == 404


def test_hunt_status_ok(test_db):
    """正常用户返回冷却字段。"""
    create_user("u1", "甲")
    with _req("/api/hunt/status/u1", method="GET",
              headers={"X-Actor-User-Id": "u1"}):
        status, payload = _unwrap(hunt_status("u1"))
    assert status == 200
    assert "can_hunt" in payload
    assert "cooldown_remaining" in payload


# ─── /api/hunt/turn/start ────────────────────────────────────────────────────

def test_hunt_turn_start_requires_actor(test_db):
    create_user("u1", "甲")
    with _req("/api/hunt/turn/start",
              json={"user_id": "u1", "monster_id": "slime"}):
        status, payload = _unwrap(hunt_turn_start())
    assert status == 401


def test_hunt_turn_start_missing_monster(test_db):
    create_user("u1", "甲")
    with _req("/api/hunt/turn/start",
              json={"user_id": "u1"},
              headers={"X-Actor-User-Id": "u1"}):
        status, payload = _unwrap(hunt_turn_start())
    assert status == 400
    assert payload["code"] == "MISSING_PARAMS"


def test_hunt_turn_start_ok(test_db, monkeypatch):
    """service 返回成功时路由透传 200。"""
    create_user("u1", "甲")

    def fake_start(user_id, monster_id, **_):
        return {"success": True, "session_id": "sess-1", "monster": {}}, 200

    import core.routes.combat as combat_routes
    monkeypatch.setattr(combat_routes, "start_hunt_session", fake_start)
    with _req("/api/hunt/turn/start",
              json={"user_id": "u1", "monster_id": "slime"},
              headers={"X-Actor-User-Id": "u1"}):
        status, payload = _unwrap(hunt_turn_start())
    assert status == 200
    assert payload["session_id"] == "sess-1"


# ─── /api/hunt/turn/action ───────────────────────────────────────────────────

def test_hunt_turn_action_requires_actor(test_db):
    create_user("u1", "甲")
    with _req("/api/hunt/turn/action",
              json={"user_id": "u1", "session_id": "s1"}):
        status, payload = _unwrap(hunt_turn_action())
    assert status == 401


def test_hunt_turn_action_missing_session(test_db):
    create_user("u1", "甲")
    with _req("/api/hunt/turn/action",
              json={"user_id": "u1"},
              headers={"X-Actor-User-Id": "u1"}):
        status, payload = _unwrap(hunt_turn_action())
    assert status == 400
    assert payload["code"] == "MISSING_PARAMS"


def test_hunt_turn_action_no_duplicate_arg(test_db, monkeypatch):
    """回归：action 参数不再导致 TypeError multiple values。"""
    create_user("u1", "甲")

    def fake_action(user_id, session_id, *, action, skill_id=None):
        return {"success": True, "action_received": action}, 200

    import core.routes.combat as combat_routes
    monkeypatch.setattr(combat_routes, "action_hunt_session", fake_action)
    with _req("/api/hunt/turn/action",
              json={"user_id": "u1", "session_id": "s1", "action": "skill"},
              headers={"X-Actor-User-Id": "u1"}):
        status, payload = _unwrap(hunt_turn_action())
    assert status == 200
    assert payload["action_received"] == "skill"
