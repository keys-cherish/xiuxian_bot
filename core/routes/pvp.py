"""PVP routes."""

from flask import Blueprint, request, jsonify

from core.routes._helpers import (
    error,
    success,
    log_action,
    parse_json_payload,
    resolve_actor_path_user_id,
    resolve_actor_user_id,
)
from core.services.pvp_service import (
    get_opponents,
    do_pvp_challenge,
    get_pvp_records,
    get_pvp_ranking,
)


pvp_bp = Blueprint("pvp", __name__)


@pvp_bp.route("/api/pvp/opponents/<user_id>", methods=["GET"])
def pvp_opponents(user_id: str):
    _, auth_error = resolve_actor_path_user_id(user_id)
    if auth_error:
        return auth_error
    limit = request.args.get("limit", 3)
    opponents = get_opponents(user_id, limit=limit)
    if opponents is None:
        return error("NOT_FOUND", "User not found", 404)
    return success(opponents=opponents)


@pvp_bp.route("/api/pvp/challenge", methods=["POST"])
def pvp_challenge():
    data, payload_error = parse_json_payload()
    if payload_error:
        return payload_error
    user_id, auth_error = resolve_actor_user_id(data)
    if auth_error:
        return auth_error
    opponent_id = data.get("opponent_id")
    request_id = data.get("request_id")
    log_action("pvp_challenge", user_id=user_id, request_id=request_id, opponent_id=opponent_id)

    if not opponent_id:
        return error("MISSING_PARAMS", "Missing parameters", 400)

    resp, http_status = do_pvp_challenge(user_id, opponent_id, request_id=request_id)
    return jsonify(resp), http_status


@pvp_bp.route("/api/pvp/records/<user_id>", methods=["GET"])
def pvp_records(user_id: str):
    _, auth_error = resolve_actor_path_user_id(user_id)
    if auth_error:
        return auth_error
    limit = request.args.get("limit", 20)
    records = get_pvp_records(user_id, limit=limit)
    return success(records=records)


@pvp_bp.route("/api/pvp/ranking", methods=["GET"])
def pvp_ranking():
    limit = request.args.get("limit", 20)
    ranking = get_pvp_ranking(limit=limit)
    return success(entries=ranking)
