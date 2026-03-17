"""sect 路由集成测试：创建-加入-晋升-踢出-宗门战-分支完整链路 + 权限/缺参校验。"""

import pytest
from flask import Flask

from core.routes.sect import (
    sect_bp,
    sect_create,
    sect_join,
    sect_leave,
    sect_promote,
    sect_kick,
    sect_donate,
    sect_war,
    sect_branch_request,
    sect_branch_join,
    sect_branch_review,
)
from core.services import sect_service
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
    app.register_blueprint(sect_bp)
    kwargs = {"method": method}
    if json is not None:
        kwargs["json"] = json
    if headers:
        kwargs["headers"] = headers
    return app.test_request_context(path, **kwargs)


def _seed_sect(sect_id="S1", leader_id="u1"):
    execute(
        """INSERT INTO sects
           (sect_id, name, description, leader_id, level, exp, fund_copper, fund_gold, max_members,
            war_wins, war_losses, last_war_time, created_at)
           VALUES (?, ?, '', ?, 1, 0, 0, 0, 10, 0, 0, 0, 0)""",
        (sect_id, "青云宗", leader_id),
    )
    execute(
        "INSERT INTO sect_members (sect_id, user_id, role, contribution, joined_at) VALUES (%s, %s, 'leader', 0, 0)",
        (sect_id, leader_id),
    )


# ─── create ──────────────────────────────────────────────────────────────────

def test_sect_create_requires_actor(test_db):
    create_user("u1", "甲")
    with _req("/api/sect/create", json={"user_id": "u1", "name": "青云宗"}):
        status, payload = _unwrap(sect_create())
    assert status == 401


def test_sect_create_actor_mismatch(test_db):
    create_user("u1", "甲")
    create_user("u2", "乙")
    with _req("/api/sect/create",
              json={"user_id": "u1", "name": "青云宗"},
              headers={"X-Actor-User-Id": "u2"}):
        status, payload = _unwrap(sect_create())
    assert status == 403
    assert payload["code"] == "FORBIDDEN"


def test_sect_create_missing_name(test_db):
    create_user("u1", "甲")
    with _req("/api/sect/create",
              json={"user_id": "u1"},
              headers={"X-Actor-User-Id": "u1"}):
        status, payload = _unwrap(sect_create())
    assert status == 400
    assert payload["code"] == "MISSING_PARAMS"


def test_sect_create_ok(test_db, monkeypatch):
    create_user("u1", "甲")
    import core.routes.sect as sect_routes
    monkeypatch.setattr(
        sect_routes, "create_sect",
        lambda uid, name, desc: ({"success": True, "sect_id": "S1"}, 200)
    )
    with _req("/api/sect/create",
              json={"user_id": "u1", "name": "青云宗"},
              headers={"X-Actor-User-Id": "u1"}):
        status, payload = _unwrap(sect_create())
    assert status == 200
    assert payload["sect_id"] == "S1"


# ─── join ────────────────────────────────────────────────────────────────────

def test_sect_join_requires_actor(test_db):
    create_user("u2", "乙")
    with _req("/api/sect/join", json={"user_id": "u2", "sect_id": "S1"}):
        status, payload = _unwrap(sect_join())
    assert status == 401


def test_sect_join_missing_sect_id(test_db):
    create_user("u2", "乙")
    with _req("/api/sect/join",
              json={"user_id": "u2"},
              headers={"X-Actor-User-Id": "u2"}):
        status, payload = _unwrap(sect_join())
    assert status == 400
    assert payload["code"] == "MISSING_PARAMS"


def test_sect_join_ok(test_db, monkeypatch):
    create_user("u1", "甲")
    create_user("u2", "乙")
    _seed_sect("S1", "u1")
    monkeypatch.setattr(
        sect_service, "join_sect",
        lambda uid, sid: ({"success": True}, 200)
    )
    with _req("/api/sect/join",
              json={"user_id": "u2", "sect_id": "S1"},
              headers={"X-Actor-User-Id": "u2"}):
        status, payload = _unwrap(sect_join())
    assert status == 200


# ─── leave ───────────────────────────────────────────────────────────────────

def test_sect_leave_requires_actor(test_db):
    create_user("u2", "乙")
    with _req("/api/sect/leave", json={"user_id": "u2"}):
        status, payload = _unwrap(sect_leave())
    assert status == 401


# ─── promote ─────────────────────────────────────────────────────────────────

def test_sect_promote_missing_target(test_db):
    create_user("u1", "甲")
    with _req("/api/sect/promote",
              json={"user_id": "u1"},
              headers={"X-Actor-User-Id": "u1"}):
        status, payload = _unwrap(sect_promote())
    assert status == 400
    assert payload["code"] == "MISSING_PARAMS"


def test_sect_promote_non_member(test_db):
    """晋升不存在成员应返回 404（直接调 service，非 mock）。"""
    create_user("u1", "甲")
    create_user("u2", "乙")
    _seed_sect("S1", "u1")
    resp, http_status = sect_service.promote_member("u1", "u2", "elder")
    assert http_status == 404
    assert resp["code"] == "NOT_FOUND"


# ─── kick ────────────────────────────────────────────────────────────────────

def test_sect_kick_missing_target(test_db):
    create_user("u1", "甲")
    with _req("/api/sect/kick",
              json={"user_id": "u1"},
              headers={"X-Actor-User-Id": "u1"}):
        status, payload = _unwrap(sect_kick())
    assert status == 400
    assert payload["code"] == "MISSING_PARAMS"


def test_sect_kick_non_member(test_db):
    create_user("u1", "甲")
    create_user("u2", "乙")
    _seed_sect("S1", "u1")
    resp, http_status = sect_service.kick_member("u1", "u2")
    assert http_status == 404
    assert resp["code"] == "NOT_FOUND"


# ─── donate ──────────────────────────────────────────────────────────────────

def test_sect_donate_requires_actor(test_db):
    create_user("u1", "甲")
    with _req("/api/sect/donate", json={"user_id": "u1", "copper": 100}):
        status, payload = _unwrap(sect_donate())
    assert status == 401


# ─── war/challenge ───────────────────────────────────────────────────────────

def test_sect_war_missing_target(test_db):
    create_user("u1", "甲")
    with _req("/api/sect/war/challenge",
              json={"user_id": "u1"},
              headers={"X-Actor-User-Id": "u1"}):
        status, payload = _unwrap(sect_war())
    assert status == 400
    assert payload["code"] == "MISSING_PARAMS"


def test_sect_war_requires_actor(test_db):
    create_user("u1", "甲")
    with _req("/api/sect/war/challenge",
              json={"user_id": "u1", "target_sect_id": "S2"}):
        status, payload = _unwrap(sect_war())
    assert status == 401


# ─── branch request ──────────────────────────────────────────────────────────

def test_sect_branch_request_missing_name(test_db):
    create_user("u1", "甲")
    with _req("/api/sect/branch/request",
              json={"user_id": "u1"},
              headers={"X-Actor-User-Id": "u1"}):
        status, payload = _unwrap(sect_branch_request())
    assert status == 400
    assert payload["code"] == "MISSING_PARAMS"


# ─── branch join ─────────────────────────────────────────────────────────────

def test_sect_branch_join_missing_branch_id(test_db):
    create_user("u1", "甲")
    with _req("/api/sect/branch/join",
              json={"user_id": "u1"},
              headers={"X-Actor-User-Id": "u1"}):
        status, payload = _unwrap(sect_branch_join())
    assert status == 400
    assert payload["code"] == "MISSING_PARAMS"


# ─── branch review ───────────────────────────────────────────────────────────

def test_sect_branch_review_missing_request_id(test_db):
    create_user("u1", "甲")
    with _req("/api/sect/branch/review",
              json={"user_id": "u1"},
              headers={"X-Actor-User-Id": "u1"}):
        status, payload = _unwrap(sect_branch_review())
    assert status == 400
    assert payload["code"] == "MISSING_PARAMS"


def test_sect_branch_review_invalid_request_id(test_db):
    create_user("u1", "甲")
    with _req("/api/sect/branch/review",
              json={"user_id": "u1", "request_id": "abc"},
              headers={"X-Actor-User-Id": "u1"}):
        status, payload = _unwrap(sect_branch_review())
    assert status == 400
    assert payload["code"] == "INVALID"
