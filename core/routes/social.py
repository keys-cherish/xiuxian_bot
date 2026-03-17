"""Social chat (论道) routes."""

from flask import Blueprint, jsonify

from core.routes._helpers import error, log_action, parse_json_payload, resolve_actor_user_id
from core.services.social_service import request_chat, accept_chat_request, reject_chat_request

social_bp = Blueprint("social", __name__)


@social_bp.route("/api/social/chat/request", methods=["POST"])
def social_chat_request():
    data, payload_error = parse_json_payload()
    if payload_error:
        return payload_error
    user_id, auth_error = resolve_actor_user_id(data)
    if auth_error:
        return auth_error
    target_name = data.get("target_name")
    target_user_id = data.get("target_user_id")
    log_action("social_chat_request", user_id=user_id, target_name=target_name, target_user_id=target_user_id)
    resp, http_status = request_chat(user_id=user_id, target_name=target_name, target_user_id=target_user_id)
    return jsonify(resp), http_status


@social_bp.route("/api/social/chat/accept", methods=["POST"])
def social_chat_accept():
    data, payload_error = parse_json_payload()
    if payload_error:
        return payload_error
    user_id, auth_error = resolve_actor_user_id(data)
    if auth_error:
        return auth_error
    request_id = data.get("request_id")
    if request_id is None:
        return error("MISSING_PARAMS", "Missing request_id", 400)
    try:
        request_id = int(request_id)
    except (TypeError, ValueError):
        return error("INVALID", "Invalid request_id", 400)
    log_action("social_chat_accept", user_id=user_id, request_id=request_id)
    resp, http_status = accept_chat_request(user_id=user_id, request_id=request_id)
    return jsonify(resp), http_status


@social_bp.route("/api/social/chat/reject", methods=["POST"])
def social_chat_reject():
    data, payload_error = parse_json_payload()
    if payload_error:
        return payload_error
    user_id, auth_error = resolve_actor_user_id(data)
    if auth_error:
        return auth_error
    request_id = data.get("request_id")
    if request_id is None:
        return error("MISSING_PARAMS", "Missing request_id", 400)
    try:
        request_id = int(request_id)
    except (TypeError, ValueError):
        return error("INVALID", "Invalid request_id", 400)
    log_action("social_chat_reject", user_id=user_id, request_id=request_id)
    resp, http_status = reject_chat_request(user_id=user_id, request_id=request_id)
    return jsonify(resp), http_status

