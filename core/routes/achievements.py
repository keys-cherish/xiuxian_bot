"""Achievement routes."""

from flask import Blueprint, jsonify

from core.routes._helpers import (
    error,
    log_action,
    parse_json_payload,
    resolve_actor_path_user_id,
    resolve_actor_user_id,
)
from core.services.achievements_service import get_achievements, claim_achievement


achievements_bp = Blueprint("achievements", __name__)


@achievements_bp.route("/api/achievements/<user_id>", methods=["GET"])
def achievements_list(user_id: str):
    _, auth_error = resolve_actor_path_user_id(user_id)
    if auth_error:
        return auth_error
    resp, http_status = get_achievements(user_id)
    return jsonify(resp), http_status


@achievements_bp.route("/api/achievements/claim", methods=["POST"])
def achievements_claim():
    data, payload_error = parse_json_payload()
    if payload_error:
        return payload_error
    user_id, auth_error = resolve_actor_user_id(data)
    if auth_error:
        return auth_error
    achievement_id = data.get("achievement_id")
    log_action("achievement_claim", user_id=user_id, achievement_id=achievement_id)
    if not user_id or not achievement_id:
        return error("MISSING_PARAMS", "Missing parameters", 400)
    resp, http_status = claim_achievement(user_id, achievement_id)
    return jsonify(resp), http_status
