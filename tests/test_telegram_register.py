import asyncio
from types import SimpleNamespace

import pytest

pytest.importorskip("telegram")

from adapters.telegram import bot as telegram_bot


class DummyMessage:
    def __init__(self):
        self.sent = []

    async def reply_text(self, text, **kwargs):
        self.sent.append((text, kwargs))
        return SimpleNamespace(chat_id=1, message_id=len(self.sent))


class DummyQuery:
    def __init__(self):
        self.message = DummyMessage()
        self.from_user = SimpleNamespace(id=123, first_name="新道友")
        self.effective_user = self.from_user


def test_do_register_accepts_callback_query(monkeypatch):
    query = DummyQuery()
    context = SimpleNamespace(application=SimpleNamespace(bot_data={}))
    calls = {}

    async def fake_http_post(url, **kwargs):
        return {"success": True, "user_id": "uid-001"}

    async def fake_reply_with_owned_panel(update, ctx, text, **kwargs):
        calls["update"] = update
        calls["context"] = ctx
        calls["text"] = text
        calls["kwargs"] = kwargs
        return SimpleNamespace(chat_id=1, message_id=1)

    monkeypatch.setattr(telegram_bot, "http_post", fake_http_post)
    monkeypatch.setattr(telegram_bot, "_reply_with_owned_panel", fake_reply_with_owned_panel)

    asyncio.run(telegram_bot.do_register(query, context, "123", "新道友", "火"))

    assert calls["update"] is query
    assert calls["context"] is context
    assert "注册成功" in calls["text"]
    assert "uid-001" in calls["text"]
