"""Gacha routes."""

from flask import Blueprint, request, jsonify

from core.routes._helpers import (
    error,
    success,
    log_action,
    parse_json_payload,
    resolve_actor_path_user_id,
    resolve_actor_user_id,
)
from core.services.gacha_service import list_banners, get_pity, pull_gacha, get_gacha_status


gacha_bp = Blueprint("gacha", __name__)


@gacha_bp.route("/api/gacha/banners", methods=["GET"])
def gacha_banners():
    banners = list_banners()
    return success(banners=banners)


@gacha_bp.route("/api/gacha/pity/<user_id>", methods=["GET"])
def gacha_pity(user_id: str):
    _, auth_error = resolve_actor_path_user_id(user_id)
    if auth_error:
        return auth_error
    banner_id = request.args.get("banner_id")
    if banner_id is None:
        return error("MISSING_PARAMS", "Missing banner_id", 400)
    try:
        banner_id = int(banner_id)
    except (TypeError, ValueError):
        return error("INVALID", "Invalid banner_id", 400)
    return success(pity=get_pity(user_id, banner_id))


@gacha_bp.route("/api/gacha/status/<user_id>", methods=["GET"])
def gacha_status(user_id: str):
    _, auth_error = resolve_actor_path_user_id(user_id)
    if auth_error:
        return auth_error
    return success(status=get_gacha_status(user_id))


@gacha_bp.route("/api/gacha/pull", methods=["POST"])
def gacha_pull():
    data, payload_error = parse_json_payload()
    if payload_error:
        return payload_error
    user_id, auth_error = resolve_actor_user_id(data)
    if auth_error:
        return auth_error
    banner_id = data.get("banner_id")
    count = data.get("count", 1)
    force_paid = bool(data.get("force_paid", False))
    log_action("gacha_pull", user_id=user_id, banner_id=banner_id, count=count)
    if banner_id is None:
        return error("MISSING_PARAMS", "Missing parameters", 400)
    try:
        banner_id = int(banner_id)
    except (TypeError, ValueError):
        return error("INVALID", "Invalid banner_id", 400)
    try:
        count = int(count or 1)
    except (TypeError, ValueError):
        return error("INVALID", "Invalid count", 400)
    resp, http_status = pull_gacha(user_id, banner_id, count=count, force_paid=force_paid)
    return jsonify(resp), http_status
