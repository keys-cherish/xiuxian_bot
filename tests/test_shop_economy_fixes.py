import time

from core.database.connection import fetch_one, execute, add_item, get_user_by_id
from core.game.items import generate_pill
from core.game.secret_realms import get_secret_realm_by_id
from core.services.settlement import settle_secret_realm_explore
from core.services.settlement_extra import settle_shop_buy, settle_use_item
from core.services.turn_battle_service import _finalize_secret_no_battle
from tests.conftest import create_user


def test_instant_secret_realm_drop_buff_not_cleared(monkeypatch, test_db):
    create_user("u1", "甲", rank=1)
    now = int(time.time())
    execute(
        "UPDATE users SET realm_drop_boost_until = %s WHERE user_id = %s",
        (now + 3600, "u1"),
    )

    monkeypatch.setattr(
        "core.services.settlement.roll_secret_realm_encounter",
        lambda realm, path="normal": {
            "type": "safe_event",
            "label": "安稳机缘",
            "monster_id": None,
            "event_text": "测试事件",
            "danger_scale": 1.0,
        },
    )
    monkeypatch.setattr(
        "core.services.settlement.roll_secret_realm_rewards",
        lambda realm, victory, user_rank, path, encounter_type, **mods: {
            "exp": 10,
            "copper": 5,
            "gold": 0,
            "drop_item_ids": [],
            "event": "ok",
        },
    )

    payload, status = settle_secret_realm_explore(
        user_id="u1",
        realm_id="mist_forest",
        path="normal",
        request_id=None,
        secret_cooldown_seconds=0,
        now=now,
    )
    assert status == 200
    assert payload.get("success")

    row = fetch_one(
        "SELECT realm_drop_boost_until FROM users WHERE user_id = %s",
        ("u1",),
    )
    assert int(row["realm_drop_boost_until"]) == now + 3600


def test_turn_secret_realm_no_battle_scores_and_buff_applied(monkeypatch, test_db):
    create_user("u1", "甲", rank=1)
    now = int(time.time())
    execute(
        "UPDATE users SET realm_drop_boost_until = %s WHERE user_id = %s",
        (now + 3600, "u1"),
    )
    realm = get_secret_realm_by_id("mist_forest")
    user = get_user_by_id("u1")

    captured = {}

    def _roll(realm, victory, user_rank, path, encounter_type, **mods):
        captured["drop_mul"] = float(mods.get("drop_mul", 1.0) or 1.0)
        return {
            "exp": 100,
            "copper": 50,
            "gold": 1,
            "drop_item_ids": [],
            "event": "ok",
        }

    monkeypatch.setattr("core.services.turn_battle_service.roll_secret_realm_rewards", _roll)

    _finalize_secret_no_battle(
        "u1",
        user,
        realm,
        "normal",
        now,
        encounter={"type": "trap", "label": "机关陷阱"},
        trap_damage=0,
    )

    row = fetch_one(
        "SELECT secret_loot_score FROM users WHERE user_id = %s",
        ("u1",),
    )
    assert int(row["secret_loot_score"] or 0) > 0
    assert captured.get("drop_mul", 1.0) > 1.0


def test_shop_buy_respects_currency_preference(monkeypatch, test_db):
    create_user("u1", "甲", rank=5)
    execute("UPDATE users SET gold = 100, copper = 0 WHERE user_id = %s", ("u1",))

    seen = {}

    def _can_buy(item_id, user_copper, user_gold, *, user_rank=1, preferred_currency=None, quantity=1):
        seen["currency"] = preferred_currency
        return True, preferred_currency or "copper", ""

    def _offer(item_id, currency=None):
        return {"item_id": item_id, "name": "测试物品", "price": 5, "currency": currency}

    monkeypatch.setattr("core.services.settlement_extra.can_buy_item", _can_buy)
    monkeypatch.setattr("core.services.settlement_extra.get_shop_offer", _offer)

    payload, status = settle_shop_buy(user_id="u1", item_id="hp_pill", quantity=1, currency="gold")
    assert status == 200
    assert seen.get("currency") == "gold"
    assert payload.get("currency") == "gold"


def test_shop_copper_price_includes_vendor_fee(test_db):
    create_user("u1", "甲", rank=5)
    execute("UPDATE users SET copper = 39, gold = 0 WHERE user_id = %s", ("u1",))

    payload, status = settle_shop_buy(user_id="u1", item_id="hp_pill", quantity=1, currency="copper")
    assert status == 400
    assert payload.get("code") == "FORBIDDEN"

    execute("UPDATE users SET copper = 100 WHERE user_id = %s", ("u1",))
    payload2, status2 = settle_shop_buy(user_id="u1", item_id="hp_pill", quantity=1, currency="copper")
    assert status2 == 200
    assert payload2.get("actual_price", 0) == payload2.get("price", 0) + payload2.get("extra_fee", 0)
    assert payload2.get("extra_fee", 0) > 0


def test_use_buff_and_breakthrough_pills(test_db):
    create_user("u1", "甲", rank=5)
    add_item("u1", generate_pill("attack_buff_pill", 1))
    add_item("u1", generate_pill("defense_buff_pill", 1))
    add_item("u1", generate_pill("cultivation_buff_pill", 1))
    add_item("u1", generate_pill("advanced_breakthrough_pill", 1))

    payload, status = settle_use_item(user_id="u1", item_id="attack_buff_pill")
    assert status == 200
    row = fetch_one(
        "SELECT attack_buff_until, attack_buff_value FROM users WHERE user_id = %s",
        ("u1",),
    )
    assert int(row["attack_buff_until"] or 0) > 0
    assert int(row["attack_buff_value"] or 0) == 20

    payload, status = settle_use_item(user_id="u1", item_id="defense_buff_pill")
    assert status == 200
    row = fetch_one(
        "SELECT defense_buff_until, defense_buff_value FROM users WHERE user_id = %s",
        ("u1",),
    )
    assert int(row["defense_buff_until"] or 0) > 0
    assert int(row["defense_buff_value"] or 0) == 20

    payload, status = settle_use_item(user_id="u1", item_id="cultivation_buff_pill")
    assert status == 200
    row = fetch_one(
        "SELECT cultivation_boost_until, cultivation_boost_pct FROM users WHERE user_id = %s",
        ("u1",),
    )
    assert int(row["cultivation_boost_until"] or 0) > 0
    assert int(row["cultivation_boost_pct"] or 0) == 50

    payload, status = settle_use_item(user_id="u1", item_id="advanced_breakthrough_pill")
    assert status == 200
    row = fetch_one(
        "SELECT breakthrough_boost_until, breakthrough_boost_pct FROM users WHERE user_id = %s",
        ("u1",),
    )
    assert int(row["breakthrough_boost_until"] or 0) > 0
    assert int(row["breakthrough_boost_pct"] or 0) == 20
