import time

from flask import Flask

from core.config import config
from core.database.connection import execute, fetch_one
from core.routes.combat import list_monsters, secret_realms_explore
from core.routes.sect import (
    sect_list,
    sect_detail,
    sect_member,
    sect_buffs,
    sect_quests,
    sect_quests_claim,
    sect_transfer,
)
from core.routes.shop import shop_buy, shop_list, use_item
from core.services.sect_service import today_local
from tests.conftest import create_user


def _unwrap(resp):
    if isinstance(resp, tuple):
        obj, status = resp
        return int(status), obj.get_json() or {}
    return int(resp.status_code), resp.get_json() or {}


def _seed_sect(sect_id: str, leader_id: str):
    execute(
        """INSERT INTO sects
           (sect_id, name, description, leader_id, level, exp, fund_copper, fund_gold, max_members,
            war_wins, war_losses, last_war_time, created_at)
           VALUES (?, ?, '', ?, 1, 0, 0, 0, 10, 0, 0, 0, ?)""",
        (sect_id, "青云宗", leader_id, int(time.time())),
    )
    execute(
        "INSERT INTO sect_members (sect_id, user_id, role, contribution, joined_at) VALUES (%s, %s, 'leader', 0, %s)",
        (sect_id, leader_id, int(time.time())),
    )


def test_shop_routes_branch_validations(test_db, monkeypatch):
    create_user("u1", "甲", rank=5)
    create_user("u2", "乙", rank=5)
    app = Flask(__name__)

    with app.test_request_context(
        "/api/shop%scurrency=copper&user_id=u1",
        method="GET",
        headers={"X-Actor-User-Id": "u2"},
    ):
        status, payload = _unwrap(shop_list())
    assert status == 403
    assert payload.get("code") == "FORBIDDEN"

    with app.test_request_context(
        "/api/shop/buy",
        method="POST",
        json={"user_id": "u1", "item_id": "hp_pill", "quantity": "bad"},
        headers={"X-Actor-User-Id": "u1"},
    ):
        status, payload = _unwrap(shop_buy())
    assert status == 400
    assert payload.get("code") == "INVALID"

    with app.test_request_context(
        "/api/shop/buy",
        method="POST",
        json={"user_id": "u1", "item_id": "hp_pill", "quantity": 1, "currency": "diamond"},
        headers={"X-Actor-User-Id": "u1"},
    ):
        status, payload = _unwrap(shop_buy())
    assert status == 400
    assert payload.get("code") == "INVALID"

    with app.test_request_context(
        "/api/item/use",
        method="POST",
        json={"user_id": "u1"},
        headers={"X-Actor-User-Id": "u1"},
    ):
        miss_status, miss_payload = _unwrap(use_item())
    assert miss_status == 400
    assert miss_payload.get("code") == "MISSING_PARAMS"

    monkeypatch.setattr(
        "core.routes.shop.settle_use_item",
        lambda user_id, item_id: ({"success": True, "user_id": user_id, "item_id": item_id}, 200),
    )
    with app.test_request_context(
        "/api/item/use",
        method="POST",
        json={"user_id": "u1", "item_id": "hp_pill"},
        headers={"X-Actor-User-Id": "u1"},
    ):
        ok_status, ok_payload = _unwrap(use_item())
    assert ok_status == 200
    assert ok_payload.get("success") is True
    assert ok_payload.get("item_id") == "hp_pill"


def test_combat_routes_business_branches(test_db, monkeypatch):
    create_user("u1", "甲", rank=17)
    app = Flask(__name__)

    captured = {}

    def _fake_monsters(rank):
        captured["rank"] = int(rank)
        return [{"id": "m1", "name": "木灵"}]

    monkeypatch.setattr("core.routes.combat.get_available_monsters", _fake_monsters)

    with app.test_request_context("/api/monsters?user_id=u1", method="GET"):
        status, payload = _unwrap(list_monsters())
    assert status == 200
    assert payload.get("success") is True
    assert payload.get("user_rank") == 17
    assert captured.get("rank") == 17

    with app.test_request_context("/api/monsters?user_id=ghost", method="GET"):
        nf_status, nf_payload = _unwrap(list_monsters())
    assert nf_status == 404
    assert nf_payload.get("success") is False

    forwarded = {}

    def _fake_explore(**kwargs):
        forwarded.update(kwargs)
        return {"success": True, "battle": False, "realm_id": kwargs.get("realm_id")}, 200

    monkeypatch.setattr("core.routes.combat.settle_secret_realm_explore", _fake_explore)
    with app.test_request_context(
        "/api/secret-realms/explore",
        method="POST",
        json={
            "user_id": "u1",
            "realm_id": "mist_forest",
            "path": "normal",
            "multi_step": True,
            "multi_step_nodes": 4,
            "request_id": "RID-SR-1",
        },
        headers={"X-Actor-User-Id": "u1"},
    ):
        exp_status, exp_payload = _unwrap(secret_realms_explore())
    assert exp_status == 200
    assert exp_payload.get("success") is True
    assert forwarded.get("user_id") == "u1"
    assert forwarded.get("realm_id") == "mist_forest"
    assert forwarded.get("multi_step") is True
    assert forwarded.get("multi_step_nodes") == 4
    assert forwarded.get("request_id") == "RID-SR-1"
    assert forwarded.get("secret_cooldown_seconds") == config.secret_realm_cooldown


def test_sect_list_detail_member_buffs_and_transfer_flow(test_db):
    create_user("u1", "宗主", rank=8)
    create_user("u2", "弟子", rank=8)
    _seed_sect("S1", "u1")
    execute(
        "INSERT INTO sect_members (sect_id, user_id, role, contribution, joined_at) VALUES (%s, %s, 'member', 0, %s)",
        ("S1", "u2", int(time.time())),
    )

    app = Flask(__name__)

    with app.test_request_context("/api/sect/list?keyword=青云", method="GET"):
        ls_status, ls_payload = _unwrap(sect_list())
    assert ls_status == 200
    assert ls_payload.get("success") is True
    assert any(row.get("sect_id") == "S1" for row in (ls_payload.get("sects") or []))

    with app.test_request_context("/api/sect/S1", method="GET"):
        dt_status, dt_payload = _unwrap(sect_detail("S1"))
    assert dt_status == 200
    assert dt_payload.get("success") is True
    member_ids = {m.get("user_id") for m in ((dt_payload.get("sect") or {}).get("members") or [])}
    assert {"u1", "u2"}.issubset(member_ids)

    with app.test_request_context(
        "/api/sect/member/u1",
        method="GET",
        headers={"X-Actor-User-Id": "u1"},
    ):
        mem_status, mem_payload = _unwrap(sect_member("u1"))
    assert mem_status == 200
    assert mem_payload.get("success") is True
    assert (mem_payload.get("sect") or {}).get("sect_id") == "S1"

    with app.test_request_context(
        "/api/sect/buffs/u1",
        method="GET",
        headers={"X-Actor-User-Id": "u1"},
    ):
        buff_status, buff_payload = _unwrap(sect_buffs("u1"))
    assert buff_status == 200
    buffs = buff_payload.get("buffs") or {}
    assert buffs.get("in_sect") is True
    assert buffs.get("sect_name") == "青云宗"

    with app.test_request_context(
        "/api/sect/transfer",
        method="POST",
        json={"user_id": "u1", "target_user_id": "u2"},
        headers={"X-Actor-User-Id": "u1"},
    ):
        tf_status, tf_payload = _unwrap(sect_transfer())
    assert tf_status == 200
    assert tf_payload.get("success") is True

    sect_row = fetch_one("SELECT leader_id FROM sects WHERE sect_id = %s", ("S1",))
    role_u1 = fetch_one("SELECT role FROM sect_members WHERE sect_id = %s AND user_id = %s", ("S1", "u1"))
    role_u2 = fetch_one("SELECT role FROM sect_members WHERE sect_id = %s AND user_id = %s", ("S1", "u2"))
    assert (sect_row or {}).get("leader_id") == "u2"
    assert (role_u2 or {}).get("role") == "leader"
    assert (role_u1 or {}).get("role") == "elder"


def test_sect_quests_claim_route_applies_rewards(test_db):
    create_user("u1", "宗主", rank=8)
    _seed_sect("S1", "u1")
    today = today_local()
    execute(
        """INSERT INTO sect_quests
           (sect_id, quest_type, assigned_date, progress, target, completed, reward_copper, reward_exp)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        ("S1", "donate", today, 10, 10, 1, 120, 60),
    )
    quest_row = fetch_one(
        "SELECT id FROM sect_quests WHERE sect_id = %s AND assigned_date = %s ORDER BY id DESC LIMIT 1",
        ("S1", today),
    )
    quest_id = int((quest_row or {}).get("id") or 0)
    assert quest_id > 0

    before = fetch_one("SELECT copper, exp FROM users WHERE user_id = %s", ("u1",))
    app = Flask(__name__)

    with app.test_request_context(
        f"/api/sect/quests/S1%suser_id=u1",
        method="GET",
        headers={"X-Actor-User-Id": "u1"},
    ):
        qs_status, qs_payload = _unwrap(sect_quests("S1"))
    assert qs_status == 200
    quests = qs_payload.get("quests") or []
    row = next((q for q in quests if int(q.get("id", 0) or 0) == quest_id), None)
    assert row is not None
    assert row.get("claimed_by_me") is False

    with app.test_request_context(
        "/api/sect/quests/claim",
        method="POST",
        json={"user_id": "u1", "quest_id": quest_id},
        headers={"X-Actor-User-Id": "u1"},
    ):
        claim_status, claim_payload = _unwrap(sect_quests_claim())
    assert claim_status == 200
    assert claim_payload.get("success") is True
    rewards = claim_payload.get("rewards") or {}
    assert int(rewards.get("copper", 0) or 0) == 120
    assert int(rewards.get("exp", 0) or 0) == 60

    after = fetch_one("SELECT copper, exp FROM users WHERE user_id = %s", ("u1",))
    assert int(after["copper"]) == int(before["copper"]) + 120
    assert int(after["exp"]) == int(before["exp"]) + 60

    with app.test_request_context(
        "/api/sect/quests/claim",
        method="POST",
        json={"user_id": "u1", "quest_id": quest_id},
        headers={"X-Actor-User-Id": "u1"},
    ):
        again_status, again_payload = _unwrap(sect_quests_claim())
    assert again_status == 400
    assert again_payload.get("code") == "CLAIMED"
