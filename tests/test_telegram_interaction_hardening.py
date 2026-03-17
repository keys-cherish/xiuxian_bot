from flask import Flask

from core.routes.events import events_claim, worldboss_attack
from core.routes.resource_conversion import convert_post
from tests.conftest import create_user

TEST_INTERNAL_TOKEN = "unit-test-internal-token"


def _unwrap_route_result(resp):
    if isinstance(resp, tuple):
        response_obj, status_code = resp
        return int(status_code), response_obj.get_json() or {}
    return int(resp.status_code), resp.get_json() or {}


def test_events_claim_requires_actor_identity(test_db):
    app = Flask(__name__)
    with app.test_request_context(
        "/api/events/claim",
        method="POST",
        json={"user_id": "u1", "event_id": "spring_festival"},
    ):
        status, payload = _unwrap_route_result(events_claim())
    assert status == 401
    assert payload.get("code") == "UNAUTHORIZED"


def test_events_claim_rejects_actor_mismatch(test_db):
    app = Flask(__name__)
    with app.test_request_context(
        "/api/events/claim",
        method="POST",
        json={"user_id": "u1", "event_id": "spring_festival"},
        headers={"X-Actor-User-Id": "u2"},
    ):
        status, payload = _unwrap_route_result(events_claim())
    assert status == 403
    assert payload.get("code") == "FORBIDDEN"


def test_worldboss_attack_requires_actor_identity(test_db):
    app = Flask(__name__)
    with app.test_request_context(
        "/api/worldboss/attack",
        method="POST",
        json={"user_id": "u1"},
    ):
        status, payload = _unwrap_route_result(worldboss_attack())
    assert status == 401
    assert payload.get("code") == "UNAUTHORIZED"


def test_worldboss_attack_rejects_actor_mismatch(test_db):
    app = Flask(__name__)
    with app.test_request_context(
        "/api/worldboss/attack",
        method="POST",
        json={"user_id": "u1"},
        headers={"X-Actor-User-Id": "u2"},
    ):
        status, payload = _unwrap_route_result(worldboss_attack())
    assert status == 403
    assert payload.get("code") == "FORBIDDEN"


def test_convert_route_logs_request_id(monkeypatch, test_db):
    create_user("u1", "甲")
    captured = {}

    def _fake_log_action(action, **kwargs):
        captured["action"] = action
        captured["kwargs"] = kwargs

    monkeypatch.setattr("core.routes.resource_conversion.log_action", _fake_log_action)

    app = Flask(__name__)
    with app.test_request_context(
        "/api/convert",
        method="POST",
        json={"user_id": "u1", "request_id": "RID-123"},
        headers={"X-Actor-User-Id": "u1"},
    ):
        status, payload = _unwrap_route_result(convert_post())

    assert status == 400
    assert payload.get("code") == "MISSING_PARAMS"
    assert captured.get("action") == "resource_convert"
    assert captured.get("kwargs", {}).get("request_id") == "RID-123"


def test_core_requires_internal_token_for_get_except_health(test_db, monkeypatch):
    monkeypatch.setenv("XXBOT_INTERNAL_API_TOKEN", TEST_INTERNAL_TOKEN)
    from core.config import config
    config.reload()
    try:
        import core.routes as routes_module

        def _register_dummy_blueprints(app):
            @app.route("/health", methods=["GET"])
            def _health():  # pragma: no cover
                return {"ok": True}

            @app.route("/api/stat/u1", methods=["GET"])
            def _stat_u1():  # pragma: no cover
                return {"success": True}

        monkeypatch.setattr(routes_module, "register_blueprints", _register_dummy_blueprints)

        from core.server import create_app
        app = create_app()

        with app.test_client() as c:
            blocked = c.get("/api/stat/u1")
            assert blocked.status_code == 401
            assert (blocked.get_json() or {}).get("code") == "UNAUTHORIZED"

            allowed_health = c.get("/health")
            assert allowed_health.status_code == 200

            authed = c.get("/api/stat/u1", headers={"X-Internal-Token": TEST_INTERNAL_TOKEN})
            assert authed.status_code == 200
            assert (authed.get_json() or {}).get("success") is True
    finally:
        monkeypatch.delenv("XXBOT_INTERNAL_API_TOKEN", raising=False)
        config.reload()
