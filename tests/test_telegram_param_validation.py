import asyncio
from types import SimpleNamespace

import pytest

pytest.importorskip("telegram")

from adapters.telegram import bot as telegram_bot


class _DummyMessage:
    def __init__(self):
        self.sent = []

    async def reply_text(self, text, **kwargs):
        self.sent.append((text, kwargs))
        return SimpleNamespace(chat_id=1, message_id=len(self.sent))


class _DummyUpdate:
    def __init__(self, uid: int = 10001):
        self.effective_user = SimpleNamespace(id=uid, first_name="Tester")
        self.message = _DummyMessage()


def _context(args):
    return SimpleNamespace(args=args, user_data={}, application=SimpleNamespace(bot_data={}))


def _patch_account_lookup(monkeypatch):
    async def _fake_http_get(url, **kwargs):
        if "/api/user/lookup" in str(url):
            return {"success": True, "user_id": "u1", "username": "Tester"}
        return {"success": True}

    async def _fake_http_post(*_args, **_kwargs):
        raise AssertionError("http_post should not be called when command params are invalid")

    monkeypatch.setattr(telegram_bot, "http_get", _fake_http_get)
    monkeypatch.setattr(telegram_bot, "http_post", _fake_http_post)


def test_sect_donate_invalid_number_returns_readable_error(monkeypatch):
    _patch_account_lookup(monkeypatch)
    update = _DummyUpdate()
    context = _context(["donate", "abc"])

    asyncio.run(telegram_bot.sect_cmd(update, context))

    text = (update.message.sent[-1][0] if update.message.sent else "")
    assert "参数错误" in text
    assert "donate" in text
    assert "服务器错误" not in text


def test_sect_branch_approve_invalid_id_returns_readable_error(monkeypatch):
    _patch_account_lookup(monkeypatch)
    update = _DummyUpdate()
    context = _context(["branch_approve", "abc"])

    asyncio.run(telegram_bot.sect_cmd(update, context))

    text = (update.message.sent[-1][0] if update.message.sent else "")
    assert "参数错误" in text
    assert "branch_approve" in text
    assert "服务器错误" not in text


def test_convert_invalid_quantity_returns_readable_error(monkeypatch):
    _patch_account_lookup(monkeypatch)
    update = _DummyUpdate()
    context = _context(["steady", "iron_ore", "abc"])

    asyncio.run(telegram_bot.convert_cmd(update, context))

    text = (update.message.sent[-1][0] if update.message.sent else "")
    assert "参数错误" in text
    assert "/convert" in text
    assert "服务器错误" not in text


def test_gacha_invalid_banner_id_returns_readable_error(monkeypatch):
    _patch_account_lookup(monkeypatch)
    update = _DummyUpdate()
    context = _context(["abc"])

    asyncio.run(telegram_bot.gacha_cmd(update, context))

    text = (update.message.sent[-1][0] if update.message.sent else "")
    assert "参数错误" in text
    assert "/gacha" in text
    assert "服务器错误" not in text


def test_gacha_duplicate_result_shows_compensation(monkeypatch):
    async def _fake_http_get(url, **kwargs):
        if "/api/user/lookup" in str(url):
            return {"success": True, "user_id": "u1", "username": "Tester"}
        return {"success": True}

    async def _fake_http_post(url, **kwargs):
        if "/api/gacha/pull" in str(url):
            return {
                "success": True,
                "pull_mode": "paid",
                "cost": {"currency": "gold", "amount": 1},
                "stamina_cost": 1,
                "results": [
                    {
                        "rarity": "SSR",
                        "item_id": "spirit_sword",
                        "item_name": "灵剑",
                        "duplicate": True,
                        "compensation": {"item_id": "immortal_stone", "item_name": "仙石", "quantity": 1},
                    }
                ],
            }
        return {"success": True}

    monkeypatch.setattr(telegram_bot, "http_get", _fake_http_get)
    monkeypatch.setattr(telegram_bot, "http_post", _fake_http_post)

    update = _DummyUpdate()
    context = _context(["1"])
    asyncio.run(telegram_bot.gacha_cmd(update, context))

    text = (update.message.sent[-1][0] if update.message.sent else "")
    assert "重复转化" in text
    assert "仙石" in text


def test_convert_menu_empty_targets_shows_unlock_hint(monkeypatch):
    async def _fake_http_get(url, **kwargs):
        if "/api/convert/options/" in str(url):
            return {
                "success": True,
                "rank": 1,
                "targets": [],
                "routes": {"steady": {"name": "稳妥转化", "desc": "desc"}},
                "configured_target_count": 2,
                "next_unlock_rank": 8,
            }
        return {"success": True}

    monkeypatch.setattr(telegram_bot, "http_get", _fake_http_get)

    text, keyboard = asyncio.run(telegram_bot._build_convert_menu("u1"))
    assert "没有可转化目标" in text
    assert "Lv.1" in text
    assert "Lv.8" in text
    assert "仅消耗铜币与精力" in text
    callbacks = [btn.callback_data for row in keyboard for btn in row]
    assert "convert_menu" in callbacks


def test_convert_route_empty_targets_shows_unlock_hint(monkeypatch):
    async def _fake_http_get(url, **kwargs):
        if "/api/convert/options/" in str(url):
            return {
                "success": True,
                "rank": 1,
                "targets": [],
                "routes": {"steady": {"name": "稳妥转化", "desc": "desc"}},
                "configured_target_count": 2,
                "next_unlock_rank": 8,
            }
        return {"success": True}

    monkeypatch.setattr(telegram_bot, "http_get", _fake_http_get)

    text, keyboard = asyncio.run(telegram_bot._build_convert_route("u1", "steady"))
    assert "没有可转化目标" in text
    assert "Lv.1" in text
    assert "Lv.8" in text
    assert "不需要背包材料" in text
    callbacks = [btn.callback_data for row in keyboard for btn in row]
    assert "convert_menu" in callbacks
