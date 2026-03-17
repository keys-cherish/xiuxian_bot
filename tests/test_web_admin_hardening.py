import web_local.app as web_app


AUTH_HEADERS = {
    "Accept": "application/json",
    "X-Admin-Password": "unit-test-admin",
}

JSON_HEADERS = {
    "Accept": "application/json",
}


def _client(monkeypatch):
    monkeypatch.setenv("XXBOT_ADMIN_PASSWORD", "unit-test-admin")
    return web_app.app.test_client()


def test_admin_api_requires_auth(monkeypatch):
    client = _client(monkeypatch)

    assert client.get("/servers/status", headers=JSON_HEADERS).status_code == 401
    assert client.post("/servers/start/core", json={}, headers=JSON_HEADERS).status_code == 401
    assert client.get("/logs/data", headers=JSON_HEADERS).status_code == 401
    assert client.get("/logs/download", headers=JSON_HEADERS).status_code == 401
    assert client.post("/database/query/users", json={"query": {}}, headers=JSON_HEADERS).status_code == 401
    assert client.post("/database/delete/not_exists_9999", json={}, headers=JSON_HEADERS).status_code == 401
    assert client.get("/database/user/not_exists_9999", headers=JSON_HEADERS).status_code == 401


def test_logs_data_no_fake_sample_fallback(monkeypatch):
    client = _client(monkeypatch)
    monkeypatch.setattr(web_app, "_collect_logs", lambda **kwargs: [])

    resp = client.get("/logs/data%ssource=foo", headers=AUTH_HEADERS)
    payload = resp.get_json() or {}

    assert resp.status_code == 200
    assert payload.get("logs") == []


def test_logs_download_uses_collected_logs(monkeypatch):
    client = _client(monkeypatch)
    marker = "WEB_AUDIT_DOWNLOAD_MARKER"
    monkeypatch.setattr(
        web_app,
        "_collect_logs",
        lambda **kwargs: [
            {
                "timestamp": "2026-03-14T12:00:00",
                "source": "telegram",
                "level": "info",
                "message": marker,
            }
        ],
    )

    resp = client.get("/logs/download%ssource=telegram", headers=AUTH_HEADERS)
    text = resp.get_data(as_text=True)

    assert resp.status_code == 200
    assert marker in text
    assert "[telegram] [INFO]" in text


def test_session_post_requires_csrf(monkeypatch):
    client = _client(monkeypatch)
    login = client.post("/admin/login", data={"password": "unit-test-admin"})
    assert login.status_code in (302, 303)

    blocked = client.post("/database/query/users", json={"query": {}}, headers=JSON_HEADERS)
    assert blocked.status_code == 403
    assert (blocked.get_json() or {}).get("message") == "CSRF 校验失败"

    with client.session_transaction() as sess:
        csrf_token = sess.get("csrf_token")
    assert csrf_token

    authed_headers = {
        **JSON_HEADERS,
        "X-CSRF-Token": csrf_token,
    }
    allowed = client.post("/database/query/users", json={"query": {}}, headers=authed_headers)
    assert allowed.status_code != 403
    assert (allowed.get_json() or {}).get("message") != "CSRF 校验失败"


def test_config_post_rejects_non_object_payload(monkeypatch):
    client = _client(monkeypatch)

    called = {"save": 0}

    def _fake_save_config(_cfg):
        called["save"] += 1

    monkeypatch.setattr(web_app, "save_config", _fake_save_config)
    resp = client.post(
        "/config",
        data="null",
        content_type="application/json",
        headers={**AUTH_HEADERS, "X-Service-Request": "1"},
    )
    payload = resp.get_json() or {}

    assert resp.status_code == 400
    assert payload.get("status") == "error"
    assert called["save"] == 0


def test_user_child_tables_cover_cleanup_targets():
    table_names = {name for name, _columns in web_app._USER_CHILD_TABLES}
    for required in (
        "battle_sessions",
        "user_realm_trials",
        "user_growth_snapshots",
        "drop_pity",
        "sect_quest_claims",
        "event_points",
        "event_point_logs",
        "event_exchange_claims",
        "event_logs",
        "economy_ledger",
    ):
        assert required in table_names


def test_header_auth_post_requires_csrf_or_service_marker(monkeypatch):
    client = _client(monkeypatch)
    blocked = client.post("/database/query/users", json={"query": {}}, headers=AUTH_HEADERS)
    payload = blocked.get_json() or {}
    assert blocked.status_code == 403
    assert payload.get("message") == "CSRF 校验失败"


def test_header_auth_service_post_allowed(monkeypatch):
    client = _client(monkeypatch)
    resp = client.post(
        "/database/query/users",
        json={"query": {}},
        headers={**AUTH_HEADERS, "X-Service-Request": "1"},
    )
    assert resp.status_code not in (401, 403)


def test_admin_template_uses_hidden_user_id_not_text_parsing():
    template_path = web_app.os.path.join(web_app.BASE_DIR, "templates", "admin.html")
    with open(template_path, encoding="utf-8") as f:
        template = f.read()
    assert 'id="selected-user-id"' in template
    assert ".textContent.replace('ID: ', '')" not in template
