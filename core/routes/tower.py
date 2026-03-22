"""Tower (trial pagoda) routes."""

from flask import Blueprint, jsonify

from core.routes._helpers import (
    error,
    success,
    log_action,
    parse_json_payload,
    resolve_actor_path_user_id,
    resolve_actor_user_id,
)
from core.services.tower_service import (
    get_tower_status,
    attempt_tower,
    reset_tower,
)

tower_bp = Blueprint("tower", __name__)


@tower_bp.route("/api/tower/status/<user_id>", methods=["GET"])
def tower_status(user_id: str):
    """获取用户古塔状态。"""
    _, auth_error = resolve_actor_path_user_id(user_id)
    if auth_error:
        return auth_error
    data = get_tower_status(user_id)
    if not data.get("success"):
        return jsonify(data), 404
    return success(**data)


@tower_bp.route("/api/tower/challenge", methods=["POST"])
def tower_challenge():
    """挑战古塔。"""
    data, payload_error = parse_json_payload()
    if payload_error:
        return payload_error
    user_id, auth_error = resolve_actor_user_id(data)
    if auth_error:
        return auth_error
    log_action("tower_challenge", user_id=user_id)
    resp, http_status = attempt_tower(user_id)
    return jsonify(resp), http_status


@tower_bp.route("/api/tower/reset", methods=["POST"])
def tower_reset():
    """重置古塔进度（消耗修为）。"""
    data, payload_error = parse_json_payload()
    if payload_error:
        return payload_error
    user_id, auth_error = resolve_actor_user_id(data)
    if auth_error:
        return auth_error
    log_action("tower_reset", user_id=user_id)
    resp, http_status = reset_tower(user_id)
    return jsonify(resp), http_status
