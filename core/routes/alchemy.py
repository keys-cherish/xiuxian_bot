"""Alchemy routes."""

from flask import Blueprint, request, jsonify

from core.routes._helpers import (
    error,
    success,
    log_action,
    parse_json_payload,
    resolve_actor_user_id,
)
from core.services.alchemy_service import get_recipes_for_user, brew_pill


alchemy_bp = Blueprint("alchemy", __name__)


@alchemy_bp.route("/api/alchemy/recipes", methods=["GET"])
def alchemy_recipes():
    user_id = request.args.get("user_id")
    if user_id:
        _, auth_error = resolve_actor_user_id({"user_id": user_id})
        if auth_error:
            return auth_error
    data = get_recipes_for_user(user_id)
    if not data.get("success"):
        return error("NOT_FOUND", data.get("message", "User not found"), 404)
    return success(**data)


@alchemy_bp.route("/api/alchemy/brew", methods=["POST"])
def alchemy_brew():
    data, payload_error = parse_json_payload()
    if payload_error:
        return payload_error
    user_id, auth_error = resolve_actor_user_id(data)
    if auth_error:
        return auth_error
    recipe_id = data.get("recipe_id")
    request_id = data.get("request_id")
    log_action("alchemy_brew", user_id=user_id, request_id=request_id, recipe_id=recipe_id)
    if not recipe_id:
        return error("MISSING_PARAMS", "Missing parameters", 400)
    resp, http_status = brew_pill(user_id, recipe_id, request_id=request_id)
    return jsonify(resp), http_status
