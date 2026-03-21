"""Audit log routes."""

from flask import Blueprint, jsonify, request

from core.config import config
from core.routes._helpers import error, resolve_actor_path_user_id
from core.services.audit_log_service import list_audit_logs


audit_bp = Blueprint("audit", __name__)


@audit_bp.route("/api/audit/logs/<user_id>", methods=["GET"])
def audit_logs_for_user(user_id: str):
    _, auth_error = resolve_actor_path_user_id(user_id)
    if auth_error:
        return auth_error
    module = request.args.get("module")
    limit = request.args.get("limit", 100)
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        return error("INVALID", "Invalid limit", 400)
    return jsonify(list_audit_logs(user_id=user_id, module=module, limit=limit))


@audit_bp.route("/api/audit/logs", methods=["GET"])
def audit_logs_admin():
    token = str(request.headers.get("X-Internal-Token", "") or "")
    if not token or token != str(config.internal_api_token or ""):
        return error("UNAUTHORIZED", "Invalid internal token", 401)
    user_id = request.args.get("user_id")
    module = request.args.get("module")
    limit = request.args.get("limit", 100)
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        return error("INVALID", "Invalid limit", 400)
    return jsonify(list_audit_logs(user_id=user_id, module=module, limit=limit))


@audit_bp.route("/api/admin/transfer_account", methods=["POST"])
def transfer_account():
    """管理员接口：将游戏数据从旧TG号迁移到新TG号。

    仅需 Internal Token 鉴权。
    请求体: {"old_telegram_id": "123456", "new_telegram_id": "789012"}

    原理: 游戏数据绑定内部 user_id，telegram_id 只是平台标识。
    迁移只改 telegram_id 字段，所有游戏数据（境界/物品/宗门等）不变。
    """
    token = str(request.headers.get("X-Internal-Token", "") or "")
    if not token or token != str(config.internal_api_token or ""):
        return error("UNAUTHORIZED", "Invalid internal token", 401)

    data = request.get_json(silent=True) or {}
    old_id = str(data.get("old_telegram_id", "") or "").strip()
    new_id = str(data.get("new_telegram_id", "") or "").strip()

    if not old_id or not new_id:
        return error("MISSING_PARAMS", "需要 old_telegram_id 和 new_telegram_id", 400)
    if old_id == new_id:
        return error("INVALID", "新旧ID不能相同", 400)

    from core.database.connection import fetch_one, execute_query

    # 检查旧号是否存在
    old_user = fetch_one(
        "SELECT user_id, telegram_id FROM users WHERE telegram_id = %s",
        (old_id,)
    )
    if not old_user:
        return error("NOT_FOUND", f"旧TG号 {old_id} 未找到对应账号", 404)

    # 检查新号是否已经绑定了其他账号
    conflict = fetch_one(
        "SELECT user_id FROM users WHERE telegram_id = %s",
        (new_id,)
    )
    if conflict:
        return error("CONFLICT",
                      f"新TG号 {new_id} 已绑定账号 {conflict['user_id']}，请先解绑或联系管理员",
                      409)

    # 执行迁移
    execute_query(
        "UPDATE users SET telegram_id = %s WHERE telegram_id = %s",
        (new_id, old_id)
    )

    from core.services.audit_log_service import log_event
    log_event(
        user_id=old_user["user_id"],
        module="admin",
        action="transfer_account",
        detail=f"telegram_id: {old_id} -> {new_id}",
    )

    return jsonify({
        "success": True,
        "message": f"迁移成功：{old_id} -> {new_id}",
        "user_id": old_user["user_id"],
    }), 200
