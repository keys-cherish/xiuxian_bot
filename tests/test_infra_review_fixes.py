import asyncio
from concurrent.futures import ThreadPoolExecutor

import pytest

from adapters.base import BaseAdapter
from core.database.connection import fetch_one, fetch_schema_version
from core.database.validators import validate_column
from core.services.account_service import register_account


def test_schema_version_set_to_latest_on_create_tables(test_db):
    assert fetch_schema_version() == 6


def test_validators_users_columns_include_extended_fields():
    for col in (
        "stamina",
        "stamina_updated_at",
        "vitals_updated_at",
        "chat_energy_today",
        "chat_energy_reset",
        "gacha_free_today",
        "gacha_paid_today",
        "gacha_daily_reset",
        "secret_loot_score",
        "alchemy_output_score",
    ):
        assert validate_column(col, "users") == col


def test_register_account_concurrent_same_platform_single_row(test_db):
    platform_id = "tg_same_id"

    def _register_once(idx: int):
        return register_account(
            platform="telegram",
            platform_id=platform_id,
            username=f"并发用户{idx}",
            element="火",
            lang="CHS",
        )

    with ThreadPoolExecutor(max_workers=2) as ex:
        results = list(ex.map(_register_once, (1, 2)))

    success_count = sum(1 for payload, status in results if status == 200 and payload.get("success"))
    assert success_count == 1

    row = fetch_one(
        "SELECT COUNT(1) AS c FROM users WHERE telegram_id = %s",
        (platform_id,),
    )
    assert int(row["c"] or 0) == 1


class _DummyAdapter(BaseAdapter):
    PLATFORM = "dummy"
    ADAPTER_VERSION = "0"

    async def start(self):
        return None

    async def stop(self):
        return None

    async def send_message(self, channel_id: str, text: str, **kwargs):
        return None

    async def reply(self, context, text: str, **kwargs):
        return None

    def register_commands(self):
        return None

    def get_token(self) -> str:
        return ""


class _FakeResp:
    status = 500

    async def json(self, content_type=None):
        raise ValueError("not json")

    async def text(self):
        return "<html>bad gateway</html>"


def test_base_adapter_parse_non_json_fallback():
    adapter = _DummyAdapter()
    payload = asyncio.run(adapter._parse_response(_FakeResp()))
    assert payload.get("code") == "NON_JSON_RESPONSE"
    assert payload.get("status_code") == 500


def test_actor_path_patterns_are_shared():
    pytest.importorskip("telegram")
    import adapters.base as base_adapter
    import adapters.telegram.bot as tg_bot

    base_patterns = [p.pattern for p in base_adapter._ACTOR_PATH_PATTERNS]
    tg_patterns = [p.pattern for p in tg_bot._ACTOR_PATH_PATTERNS]
    assert base_patterns == tg_patterns


def test_telegram_request_json_non_json_fallback(monkeypatch):
    pytest.importorskip("telegram")
    import adapters.telegram.bot as tg_bot

    class _FakeReqCtx:
        async def __aenter__(self):
            return _FakeResp()

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class _FakeSession:
        def request(self, method, url, **kwargs):
            return _FakeReqCtx()

    async def _fake_get_http_session():
        return _FakeSession()

    monkeypatch.setattr(tg_bot, "_get_http_session", _fake_get_http_session)
    payload = asyncio.run(tg_bot._request_json("GET", "http://127.0.0.1/test"))
    assert payload.get("code") == "NON_JSON_RESPONSE"
    assert payload.get("status_code") == 500


def test_telegram_shop_render_handles_missing_name_and_price():
    pytest.importorskip("telegram")
    import adapters.telegram.bot as tg_bot

    item = {"item_id": "iron_ore", "actual_price": 33, "currency": "copper"}
    text = tg_bot._build_shop_text([item], rank=1, category="all")
    keyboard = tg_bot._build_shop_keyboard("all", [item])

    assert "33" in text
    assert ("iron_ore" in text) or ("铁矿石" in text)
    assert keyboard and keyboard[0] and keyboard[0][0].callback_data == "buy_copper_iron_ore"
    assert "33" in keyboard[0][0].text


def test_start_server_returns_false_when_bind_fails(monkeypatch):
    import core.server as server

    monkeypatch.setattr(server, "initialize_core_components", lambda: True)

    def _fake_run_core_server():
        server._server_start_error = RuntimeError("bind failed")
        if server._server_start_event is not None:
            server._server_start_event.set()

    monkeypatch.setattr(server, "run_core_server", _fake_run_core_server)
    server.server_running = False
    server._wsgi_server = None

    assert server.start_server() is False
