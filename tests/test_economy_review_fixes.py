from flask import Flask

from core.database.connection import add_item, execute, fetch_one
from core.game.items import Quality, generate_equipment, generate_material, get_item_by_id
from core.routes.equipment import equip_item
from core.routes.resource_conversion import convert_post
from core.routes.skills import skill_learn
from core.services.forge_service import forge, forge_targeted
from core.services.resource_conversion_service import convert_resources, list_conversion_options
from tests.conftest import create_user


def _unwrap_route_result(resp):
    if isinstance(resp, tuple):
        response_obj, status_code = resp
        return int(status_code), response_obj.get_json() or {}
    return int(resp.status_code), resp.get_json() or {}


def _sum_material_qty(user_id: str, item_id: str) -> int:
    row = fetch_one(
        "SELECT SUM(quantity) AS qty FROM items WHERE user_id = %s AND item_id = %s AND item_type = 'material'",
        (user_id, item_id),
    )
    return int(row["qty"] or 0) if row else 0


def test_forge_invalid_pool_no_resource_deduction(test_db):
    create_user("u1", "甲", rank=10)
    add_item("u1", generate_material("iron_ore", 20))
    payload, status = forge(
        user_id="u1",
        cfg={
            "enabled": True,
            "base_cost_copper": 100,
            "material_item_id": "iron_ore",
            "material_need": 8,
            "reward_pool": [{"item_id": "not_exists_item", "weight": 1}],
        },
    )
    assert status == 500
    assert payload.get("code") == "CONFIG"
    user = fetch_one("SELECT copper, stamina FROM users WHERE user_id = %s", ("u1",))
    assert int(user["copper"]) == 1000
    assert int(user["stamina"]) == 24
    assert _sum_material_qty("u1", "iron_ore") == 20


def test_forge_uses_stacked_material_rows(test_db):
    create_user("u1", "甲", rank=10)
    add_item("u1", generate_material("iron_ore", 5))
    add_item("u1", generate_material("iron_ore", 5))
    payload, status = forge(
        user_id="u1",
        cfg={
            "enabled": True,
            "base_cost_copper": 100,
            "material_item_id": "iron_ore",
            "material_need": 8,
            "reward_pool": [{"item_id": "small_exp_pill", "weight": 1, "qty": 1}],
        },
    )
    assert status == 200
    assert payload.get("success") is True
    assert _sum_material_qty("u1", "iron_ore") == 2
    user = fetch_one("SELECT copper, stamina FROM users WHERE user_id = %s", ("u1",))
    assert int(user["copper"]) == 900
    assert int(user["stamina"]) == 23


def test_forge_material_failure_rolls_back_stamina_and_copper(monkeypatch, test_db):
    create_user("u1", "甲", rank=10)
    add_item("u1", generate_material("iron_ore", 20))

    monkeypatch.setattr(
        "core.services.forge_service._deduct_material",
        lambda cur, user_id, item_id, quantity: (_ for _ in ()).throw(ValueError("INSUFFICIENT_MATERIAL")),
    )

    payload, status = forge(
        user_id="u1",
        cfg={
            "enabled": True,
            "base_cost_copper": 100,
            "material_item_id": "iron_ore",
            "material_need": 8,
            "reward_pool": [{"item_id": "small_exp_pill", "weight": 1, "qty": 1}],
        },
    )
    assert status == 400
    assert payload.get("code") == "INSUFFICIENT_MATERIAL"
    user = fetch_one("SELECT copper, stamina FROM users WHERE user_id = %s", ("u1",))
    assert int(user["copper"]) == 1000
    assert int(user["stamina"]) == 24
    assert _sum_material_qty("u1", "iron_ore") == 20


def test_forge_targeted_uses_stacked_material_rows(test_db):
    create_user("u1", "甲", rank=10)
    execute(
        "INSERT INTO codex_items (user_id, item_id, first_seen_at, last_seen_at, total_obtained) VALUES (%s, %s, %s, %s, %s)",
        ("u1", "spirit_sword", 1, 1, 1),
    )
    add_item("u1", generate_material("iron_ore", 8))
    add_item("u1", generate_material("iron_ore", 10))
    payload, status = forge_targeted(
        user_id="u1",
        item_id="spirit_sword",
        cfg={
            "base_cost_copper": 100,
            "material_need": 8,
            "material_item_id": "iron_ore",
        },
    )
    assert status == 200
    assert payload.get("success") is True
    assert _sum_material_qty("u1", "iron_ore") == 2
    user = fetch_one("SELECT copper, stamina FROM users WHERE user_id = %s", ("u1",))
    assert int(user["copper"]) == 800
    assert int(user["stamina"]) == 23


def test_skill_learn_active_obeys_two_equip_limit(test_db):
    create_user("u1", "甲", rank=8)
    execute("UPDATE users SET copper = 100000, gold = 20 WHERE user_id = %s", ("u1",))
    app = Flask(__name__)

    for skill_id in ("qixue_slash", "flame_burst", "fire_blast"):
        with app.test_request_context(
            "/api/skills/learn",
            method="POST",
            json={"user_id": "u1", "skill_id": skill_id},
            headers={"X-Actor-User-Id": "u1"},
        ):
            status, payload = _unwrap_route_result(skill_learn())
            assert status == 200, payload

    row = fetch_one(
        """
        SELECT COUNT(1) AS c
        FROM user_skills
        WHERE user_id = ?
          AND equipped = 1
          AND skill_id IN ('qixue_slash', 'flame_burst', 'fire_blast')
        """,
        ("u1",),
    )
    assert int(row["c"]) == 2


def test_equip_item_rejects_rank_too_low(test_db):
    create_user("u1", "甲", rank=1)
    base = get_item_by_id("spirit_sword")
    item_db_id = add_item("u1", generate_equipment(base, Quality.COMMON, 1))
    app = Flask(__name__)
    with app.test_request_context(
        "/api/equip",
        method="POST",
        json={"user_id": "u1", "item_id": item_db_id},
        headers={"X-Actor-User-Id": "u1"},
    ):
        status, payload = _unwrap_route_result(equip_item())
    assert status == 400
    assert "境界不足" in str(payload.get("message", ""))


def test_equip_item_rejects_duplicate_accessory(test_db):
    create_user("u1", "甲", rank=10)
    base = get_item_by_id("spirit_ring")
    item_db_id = add_item("u1", generate_equipment(base, Quality.COMMON, 1))
    app = Flask(__name__)

    with app.test_request_context(
        "/api/equip",
        method="POST",
        json={"user_id": "u1", "item_id": item_db_id},
        headers={"X-Actor-User-Id": "u1"},
    ):
        status1, payload1 = _unwrap_route_result(equip_item())
    assert status1 == 200, payload1

    with app.test_request_context(
        "/api/equip",
        method="POST",
        json={"user_id": "u1", "item_id": item_db_id},
        headers={"X-Actor-User-Id": "u1"},
    ):
        status2, payload2 = _unwrap_route_result(equip_item())
    assert status2 == 400
    assert "已装备" in str(payload2.get("message", ""))
    user = fetch_one("SELECT equipped_accessory2 FROM users WHERE user_id = %s", ("u1",))
    assert user.get("equipped_accessory2") is None


def test_convert_route_rejects_non_positive_quantity(test_db):
    create_user("u1", "甲", rank=10)
    app = Flask(__name__)
    with app.test_request_context(
        "/api/convert",
        method="POST",
        json={"user_id": "u1", "target_item_id": "spirit_herb", "quantity": 0, "route": "steady"},
        headers={"X-Actor-User-Id": "u1"},
    ):
        status, payload = _unwrap_route_result(convert_post())
    assert status == 400
    assert payload.get("code") == "INVALID"


def test_convert_service_rejects_non_positive_quantity(test_db):
    create_user("u1", "甲", rank=10)
    payload, status = convert_resources(
        user_id="u1",
        target_item_id="spirit_herb",
        quantity=-2,
        route="steady",
        request_id=None,
    )
    assert status == 400
    assert payload.get("code") == "INVALID"


def test_convert_stamina_cost_scales_with_batch(test_db):
    create_user("u1", "甲", rank=10)
    execute("UPDATE users SET copper = 10000, stamina = 5 WHERE user_id = %s", ("u1",))
    payload, status = convert_resources(
        user_id="u1",
        target_item_id="spirit_herb",
        quantity=6,
        route="steady",
        request_id=None,
    )
    assert status == 200
    assert payload.get("stamina_cost") == 2
    row = fetch_one("SELECT stamina FROM users WHERE user_id = %s", ("u1",))
    assert int(row["stamina"]) == 3


def test_convert_risky_floor_for_small_qty(monkeypatch, test_db):
    create_user("u1", "甲", rank=10)
    execute("UPDATE users SET copper = 10000, stamina = 5 WHERE user_id = %s", ("u1",))

    monkeypatch.setattr("core.services.resource_conversion_service.random.random", lambda: 0.99)

    payload, status = convert_resources(
        user_id="u1",
        target_item_id="spirit_herb",
        quantity=1,
        route="risky",
        request_id=None,
    )
    assert status == 200
    assert payload.get("convert_success") is False
    assert payload.get("output_quantity", 0) >= 1


def test_convert_options_empty_targets_report_next_unlock_rank(monkeypatch, test_db):
    create_user("u1", "甲", rank=5)

    monkeypatch.setattr(
        "core.services.resource_conversion_service.get_resource_conversion_config",
        lambda: {
            "routes": {
                "steady": {"name": "稳妥转化", "desc": "", "cost_mult": 1.1, "output_mult": 1.0, "success_rate": 1.0, "fail_output_mult": 1.0, "requires_catalyst": False},
                "risky": {"name": "投机转化", "desc": "", "cost_mult": 0.95, "output_mult": 1.6, "success_rate": 0.45, "fail_output_mult": 0.4, "requires_catalyst": False},
                "focused": {"name": "专精转化", "desc": "", "cost_mult": 1.05, "output_mult": 1.25, "success_rate": 1.0, "fail_output_mult": 1.0, "requires_catalyst": True},
            },
            "targets": [
                {"item_id": "spirit_herb", "min_rank": 8, "base_copper": 120},
                {"item_id": "demon_core", "min_rank": 10, "base_copper": 360},
            ],
            "focused_catalyst": {"spirit_herb": "herb", "demon_core": "spirit_stone"},
            "max_batch": 20,
            "focused_catalyst_per_batch": 1,
            "stamina_batch_size": 5,
        },
    )

    payload, status = list_conversion_options("u1")
    assert status == 200
    assert payload.get("success") is True
    assert payload.get("targets") == []
    assert int(payload.get("configured_target_count", 0)) == 2
    assert int(payload.get("next_unlock_rank", 0)) == 8
