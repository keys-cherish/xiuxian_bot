from concurrent.futures import ThreadPoolExecutor

from flask import Flask

from core.database.connection import fetch_one, execute, upsert_quest
from core.database.migrations import get_cached_response, save_response
from core.game.items import get_item_by_id
from core.routes.shop import shop_buy, shop_list
from core.services.forge_service import decompose_item
from core.services.quests_service import today_str
from core.services.settlement import settle_quest_claim
from core.services.settlement_extra import settle_shop_buy
from tests.conftest import create_user


def _unwrap_route_result(resp):
    if isinstance(resp, tuple):
        response_obj, status_code = resp
        return int(status_code), response_obj.get_json() or {}
    return int(resp.status_code), resp.get_json() or {}


def test_shop_buy_requires_actor_identity(test_db):
    app = Flask(__name__)
    with app.test_request_context(
        "/api/shop/buy",
        method="POST",
        json={"user_id": "u1", "item_id": "hp_pill", "quantity": 1},
    ):
        status, payload = _unwrap_route_result(shop_buy())
    assert status == 401
    assert payload.get("code") == "UNAUTHORIZED"


def test_shop_buy_rejects_actor_user_mismatch(test_db):
    app = Flask(__name__)
    with app.test_request_context(
        "/api/shop/buy",
        method="POST",
        json={"user_id": "u1", "item_id": "hp_pill", "quantity": 1},
        headers={"X-Actor-User-Id": "u2"},
    ):
        status, payload = _unwrap_route_result(shop_buy())
    assert status == 403
    assert payload.get("code") == "FORBIDDEN"


def test_shop_list_hydrates_missing_name_without_user(monkeypatch, test_db):
    monkeypatch.setattr(
        "core.routes.shop.get_shop_items",
        lambda currency: [{"item_id": "iron_ore", "price": 12, "currency": currency}],
    )
    monkeypatch.setattr(
        "core.routes.shop.get_item_by_id",
        lambda item_id: {"name": "铁矿石"} if item_id == "iron_ore" else {},
    )

    app = Flask(__name__)
    with app.test_request_context("/api/shop?currency=copper", method="GET"):
        status, payload = _unwrap_route_result(shop_list())

    assert status == 200
    assert payload.get("success") is True
    items = payload.get("items") or []
    assert items and items[0].get("name") == "铁矿石"


def test_shop_list_hydrates_missing_name_with_user_limit(monkeypatch, test_db):
    create_user("u1", "甲")
    monkeypatch.setattr(
        "core.routes.shop.get_shop_items",
        lambda currency: [{"item_id": "herb", "price": 8, "currency": currency}],
    )
    monkeypatch.setattr(
        "core.routes.shop.get_item_by_id",
        lambda item_id: {"name": "草药"} if item_id == "herb" else {},
    )
    monkeypatch.setattr("core.routes.shop.get_shop_remaining_limit", lambda *_args, **_kwargs: 5)

    app = Flask(__name__)
    with app.test_request_context(
        "/api/shop%scurrency=copper&user_id=u1",
        method="GET",
        headers={"X-Actor-User-Id": "u1"},
    ):
        status, payload = _unwrap_route_result(shop_list())

    assert status == 200
    assert payload.get("success") is True
    items = payload.get("items") or []
    assert items and items[0].get("name") == "草药"
    assert int(items[0].get("remaining_limit", 0)) == 5


def test_request_dedup_scoped_by_user_and_action(test_db):
    create_user("u1", "甲")
    create_user("u2", "乙")

    save_response("RID-1", "u1", "quest_claim", {"success": True, "source": "u1"})
    save_response("RID-1", "u2", "quest_claim", {"success": True, "source": "u2"})

    u1_cached = get_cached_response("RID-1", user_id="u1", action="quest_claim")
    u2_cached = get_cached_response("RID-1", user_id="u2", action="quest_claim")
    assert u1_cached and u1_cached.get("source") == "u1"
    assert u2_cached and u2_cached.get("source") == "u2"

    row = fetch_one(
        "SELECT COUNT(1) AS c FROM request_dedup WHERE request_id = %s",
        ("RID-1",),
    )
    assert int(row["c"]) == 2


def test_quest_claim_concurrent_single_success(test_db):
    create_user("u1", "甲")
    today = today_str()
    upsert_quest("u1", "daily_signin", today, progress=1, goal=1)

    def _claim_once():
        return settle_quest_claim(
            user_id="u1",
            quest_id="daily_signin",
            request_id=None,
            claim_cooldown_seconds=0,
            today=today,
            now=123456,
        )

    with ThreadPoolExecutor(max_workers=4) as ex:
        results = list(ex.map(lambda _: _claim_once(), range(4)))

    success_payloads = [payload for payload, status in results if status == 200 and payload.get("success")]
    assert len(success_payloads) == 1

    reward = success_payloads[0]["rewards"]
    user = fetch_one("SELECT copper, exp FROM users WHERE user_id = %s", ("u1",))
    assert int(user["copper"]) == 1000 + int(reward.get("copper", 0) or 0)
    assert int(user["exp"]) == 1000 + int(reward.get("exp", 0) or 0)

    quest = fetch_one(
        "SELECT claimed FROM user_quests WHERE user_id = %s AND quest_id = %s AND assigned_date = %s",
        ("u1", "daily_signin", today),
    )
    assert int(quest["claimed"]) == 1




def test_shop_limit_concurrent_not_exceed(monkeypatch, test_db):
    create_user("u1", "甲")

    monkeypatch.setattr(
        "core.services.settlement_extra.can_buy_item",
        lambda item_id, user_copper, user_gold, user_rank=1, preferred_currency=None, quantity=1: (True, "copper", ""),
    )
    monkeypatch.setattr(
        "core.services.settlement_extra.get_shop_offer",
        lambda item_id, currency=None: {
            "item_id": item_id,
            "name": "回血丹",
            "price": 10,
            "currency": "copper",
            "limit": 2,
            "limit_period": "day",
        },
    )

    def _buy_once():
        return settle_shop_buy(user_id="u1", item_id="hp_pill", quantity=2)

    with ThreadPoolExecutor(max_workers=2) as ex:
        results = list(ex.map(lambda _: _buy_once(), range(2)))

    success_count = sum(1 for payload, status in results if status == 200 and payload.get("success"))
    limit_failures = sum(1 for payload, status in results if status == 400 and payload.get("code") == "LIMIT")
    assert success_count == 1
    assert limit_failures == 1

    limit_row = fetch_one(
        "SELECT quantity FROM shop_purchase_limits WHERE user_id = %s AND item_id = %s ORDER BY id DESC LIMIT 1",
        ("u1", "hp_pill"),
    )
    assert limit_row is not None
    assert int(limit_row["quantity"]) == 2

    bag_row = fetch_one(
        "SELECT SUM(quantity) AS qty FROM items WHERE user_id = %s AND item_id = %s",
        ("u1", "hp_pill"),
    )
    assert int(bag_row["qty"] or 0) == 2


def test_decompose_concurrent_single_success(test_db):
    create_user("u1", "甲")
    item_db_id = execute(
        """INSERT INTO items (user_id, item_id, item_name, item_type, quality, quantity, level,
           attack_bonus, defense_bonus, hp_bonus, mp_bonus,
           first_round_reduction_pct, crit_heal_pct, element_damage_pct, low_hp_shield_pct)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            "u1",
            "wooden_sword",
            "木剑",
            "weapon",
            "common",
            1,
            1,
            1,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
        ),
    )

    def _decompose_once():
        return decompose_item(user_id="u1", item_db_id=item_db_id)

    with ThreadPoolExecutor(max_workers=2) as ex:
        results = list(ex.map(lambda _: _decompose_once(), range(2)))

    success_count = sum(1 for payload, status in results if status == 200 and payload.get("success"))
    not_found_count = sum(1 for payload, status in results if status == 404 and payload.get("code") == "NOT_FOUND")
    assert success_count == 1
    assert not_found_count == 1

    base = get_item_by_id("wooden_sword") or {}
    min_rank = int(base.get("min_rank", 1) or 1)
    expected_copper = max(40, min_rank * 25)

    user = fetch_one("SELECT copper FROM users WHERE user_id = %s", ("u1",))
    assert int(user["copper"]) == 1000 + expected_copper
