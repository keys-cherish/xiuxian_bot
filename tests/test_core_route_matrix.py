from flask import Flask

from core.routes.alchemy import alchemy_brew
from core.routes.combat import hunt
from core.routes.cultivation import breakthrough
from core.routes.equipment import user_items
from core.routes.gacha import gacha_pull
from core.routes.user import user_status


def _unwrap_route_result(resp):
    if isinstance(resp, tuple):
        response_obj, status_code = resp
        return int(status_code), response_obj.get_json() or {}
    return int(resp.status_code), resp.get_json() or {}


def test_combat_hunt_invalid_payload_returns_standard_error(test_db):
    app = Flask(__name__)
    with app.test_request_context(
        "/api/hunt",
        method="POST",
        data="not-json",
        content_type="text/plain",
        headers={"X-Actor-User-Id": "u1"},
    ):
        status, payload = _unwrap_route_result(hunt())
    assert status == 400
    assert payload.get("code") == "INVALID_PAYLOAD"


def test_cultivation_breakthrough_requires_actor_identity(test_db):
    app = Flask(__name__)
    with app.test_request_context(
        "/api/breakthrough",
        method="POST",
        json={"user_id": "u1", "use_pill": False},
    ):
        status, payload = _unwrap_route_result(breakthrough())
    assert status == 401
    assert payload.get("code") == "UNAUTHORIZED"


def test_equipment_items_path_actor_mismatch_forbidden(test_db):
    app = Flask(__name__)
    with app.test_request_context(
        "/api/items/u1",
        method="GET",
        headers={"X-Actor-User-Id": "u2"},
    ):
        status, payload = _unwrap_route_result(user_items("u1"))
    assert status == 403
    assert payload.get("code") == "FORBIDDEN"


def test_gacha_pull_missing_banner_id_returns_missing_params(test_db):
    app = Flask(__name__)
    with app.test_request_context(
        "/api/gacha/pull",
        method="POST",
        json={"user_id": "u1"},
        headers={"X-Actor-User-Id": "u1"},
    ):
        status, payload = _unwrap_route_result(gacha_pull())
    assert status == 400
    assert payload.get("code") == "MISSING_PARAMS"


def test_alchemy_brew_missing_recipe_returns_missing_params(test_db):
    app = Flask(__name__)
    with app.test_request_context(
        "/api/alchemy/brew",
        method="POST",
        json={"user_id": "u1"},
        headers={"X-Actor-User-Id": "u1"},
    ):
        status, payload = _unwrap_route_result(alchemy_brew())
    assert status == 400
    assert payload.get("code") == "MISSING_PARAMS"


def test_stat_path_reject_actor_mismatch(test_db):
    app = Flask(__name__)
    with app.test_request_context(
        "/api/stat/u1",
        method="GET",
        headers={"X-Actor-User-Id": "u2"},
    ):
        stat_status, stat_payload = _unwrap_route_result(user_status("u1"))
    assert stat_status == 403
    assert stat_payload.get("code") == "FORBIDDEN"
