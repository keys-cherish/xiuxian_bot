"""任务路由。"""

from flask import Blueprint, request, jsonify

from core.routes._helpers import (
    error,
    success,
    log_action,
    parse_json_payload,
    resolve_actor_path_user_id,
    resolve_actor_user_id,
)
from core.config import config
from core.database.connection import get_user_by_id
from core.game.quests import get_all_quest_defs
from core.services.quests_service import today_str, ensure_daily_quests
from core.services.settlement import settle_quest_claim, settle_quest_claim_all
from core.database.connection import get_user_quests

quests_bp = Blueprint("quests", __name__)


@quests_bp.route("/api/quests/<user_id>", methods=["GET"])
def quests_list(user_id):
    """获取每日任务列表"""
    _, auth_error = resolve_actor_path_user_id(user_id)
    if auth_error:
        return auth_error
    user = get_user_by_id(user_id)
    if not user:
        return error("ERROR", "User not found", 404)
    ensure_daily_quests(user_id)
    today = today_str()
    rows = get_user_quests(user_id, today)
    defs = get_all_quest_defs()
    return success(
        quests=[dict(r) for r in rows],
        quest_defs=defs,
    )


@quests_bp.route("/api/quests/claim", methods=["POST"])
def quest_claim():
    """领取任务奖励"""
    data, payload_error = parse_json_payload()
    if payload_error:
        return payload_error
    user_id, auth_error = resolve_actor_user_id(data)
    if auth_error:
        return auth_error
    quest_id = data.get("quest_id")
    request_id = data.get("request_id")
    log_action("quest_claim", user_id=user_id, request_id=request_id, quest_id=quest_id)

    if not quest_id:
        return error("MISSING_PARAMS", "Missing parameters", 400)

    resp, http_status = settle_quest_claim(
        user_id=user_id,
        quest_id=quest_id,
        request_id=request_id,
        claim_cooldown_seconds=config.quest_claim_cooldown,
        today=today_str(),
    )
    return jsonify(resp), http_status


@quests_bp.route("/api/quests/claim_all", methods=["POST"])
def quest_claim_all():
    """一键领取已完成任务奖励"""
    data, payload_error = parse_json_payload()
    if payload_error:
        return payload_error
    user_id, auth_error = resolve_actor_user_id(data)
    if auth_error:
        return auth_error
    request_id = data.get("request_id")
    log_action("quest_claim_all", user_id=user_id, request_id=request_id)

    resp, http_status = settle_quest_claim_all(
        user_id=user_id,
        request_id=request_id,
        claim_cooldown_seconds=config.quest_claim_cooldown,
        today=today_str(),
    )
    return jsonify(resp), http_status
