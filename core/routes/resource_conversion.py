"""资源转化路由。"""

from flask import Blueprint, request, jsonify

from core.routes._helpers import (
    error,
    log_action,
    parse_json_payload,
    resolve_actor_path_user_id,
    resolve_actor_user_id,
)
from core.services.resource_conversion_service import list_conversion_options, convert_resources

convert_bp = Blueprint("convert", __name__)


@convert_bp.route("/api/convert/options/<user_id>", methods=["GET"])
def convert_options(user_id: str):
    _, auth_error = resolve_actor_path_user_id(user_id)
    if auth_error:
        return auth_error
    resp, http_status = list_conversion_options(user_id)
    return jsonify(resp), http_status


@convert_bp.route("/api/convert", methods=["POST"])
def convert_post():
    data, payload_error = parse_json_payload()
    if payload_error:
        return payload_error
    user_id, auth_error = resolve_actor_user_id(data)
    if auth_error:
        return auth_error
    target_item_id = data.get("target_item_id")
    quantity = data.get("quantity", 1)
    route = data.get("route", "steady")
    request_id = data.get("request_id")
    log_action(
        "resource_convert",
        user_id=user_id,
        request_id=request_id,
        target_item_id=target_item_id,
        route=route,
    )

    if not target_item_id:
        return error("MISSING_PARAMS", "Missing parameters", 400)

    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        return error("INVALID", "Invalid quantity", 400)
    if quantity <= 0:
        return error("INVALID", "quantity must be positive", 400)

    resp, http_status = convert_resources(
        user_id=user_id,
        target_item_id=str(target_item_id),
        quantity=quantity,
        route=str(route or "steady"),
        request_id=request_id,
    )
    return jsonify(resp), http_status
