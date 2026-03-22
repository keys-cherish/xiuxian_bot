"""
core/routes/garden.py
药园（宗门灵田）API 路由。
"""

from flask import Blueprint, request, jsonify

from core.routes._helpers import (
    error,
    success,
    log_action,
    parse_json_payload,
    resolve_actor_user_id,
    resolve_actor_path_user_id,
)
from core.services.herb_garden_service import (
    get_garden_status,
    get_plots,
    plant_herb,
    harvest_herb,
    harvest_all,
    water_plot,
    water_all,
    remove_pest,
    remove_pest_all,
    remove_dead,
    remove_dead_all,
    get_herb_list,
)

garden_bp = Blueprint("garden", __name__)


# ── GET /api/garden/herbs — 可种植灵植列表 ──

@garden_bp.route("/api/garden/herbs", methods=["GET"])
def garden_herbs():
    """获取所有可种植灵植列表。"""
    herbs = get_herb_list()
    return success(herbs=herbs)


# ── GET /api/garden/<user_id> — 药园状态 ──

@garden_bp.route("/api/garden/<user_id>", methods=["GET"])
def garden_status(user_id: str):
    """获取指定用户的药园状态。"""
    uid, auth_err = resolve_actor_path_user_id(user_id)
    if auth_err:
        return auth_err

    result = get_garden_status(uid)
    if result.get("error"):
        return error(result["error"], result.get("message", ""), 404)
    return success(**result)


# ── POST /api/garden/plant — 种植 ──

@garden_bp.route("/api/garden/plant", methods=["POST"])
def garden_plant():
    """种植灵植。body: { user_id, plot_index, herb_name }"""
    data, payload_err = parse_json_payload()
    if payload_err:
        return payload_err
    uid, auth_err = resolve_actor_user_id(data)
    if auth_err:
        return auth_err

    plot_index = data.get("plot_index")
    herb_name = data.get("herb_name", "").strip()
    request_id = data.get("request_id")

    log_action("garden_plant", user_id=uid, request_id=request_id,
               herb_name=herb_name, plot_index=plot_index)

    if plot_index is None or herb_name == "":
        return error("MISSING_PARAMS", "Missing plot_index or herb_name", 400)

    try:
        plot_index = int(plot_index)
    except (TypeError, ValueError):
        return error("INVALID", "Invalid plot_index", 400)

    result = plant_herb(uid, plot_index, herb_name)
    if not result.get("success"):
        return error(result.get("code", "PLANT_FAILED"), result.get("message", ""), 400)
    return success(**result)


# ── POST /api/garden/harvest — 收获 ──

@garden_bp.route("/api/garden/harvest", methods=["POST"])
def garden_harvest():
    """收获灵植。body: { user_id, plot_index } 或 { user_id, plot_index: "all" }"""
    data, payload_err = parse_json_payload()
    if payload_err:
        return payload_err
    uid, auth_err = resolve_actor_user_id(data)
    if auth_err:
        return auth_err

    plot_index = data.get("plot_index")
    request_id = data.get("request_id")

    log_action("garden_harvest", user_id=uid, request_id=request_id, plot_index=plot_index)

    if plot_index == "all" or plot_index is None:
        result = harvest_all(uid)
    else:
        try:
            plot_index = int(plot_index)
        except (TypeError, ValueError):
            return error("INVALID", "Invalid plot_index", 400)
        result = harvest_herb(uid, plot_index)

    if not result.get("success"):
        return error(result.get("code", "HARVEST_FAILED"), result.get("message", ""), 400)
    return success(**result)


# ── POST /api/garden/water — 浇水 ──

@garden_bp.route("/api/garden/water", methods=["POST"])
def garden_water():
    """浇水。body: { user_id, plot_index } 或 { user_id, plot_index: "all" }"""
    data, payload_err = parse_json_payload()
    if payload_err:
        return payload_err
    uid, auth_err = resolve_actor_user_id(data)
    if auth_err:
        return auth_err

    plot_index = data.get("plot_index")
    request_id = data.get("request_id")

    log_action("garden_water", user_id=uid, request_id=request_id, plot_index=plot_index)

    if plot_index == "all" or plot_index is None:
        result = water_all(uid)
    else:
        try:
            plot_index = int(plot_index)
        except (TypeError, ValueError):
            return error("INVALID", "Invalid plot_index", 400)
        result = water_plot(uid, plot_index)

    if not result.get("success"):
        return error(result.get("code", "WATER_FAILED"), result.get("message", ""), 400)
    return success(**result)


# ── POST /api/garden/remove-pest — 除虫 ──

@garden_bp.route("/api/garden/remove-pest", methods=["POST"])
def garden_remove_pest():
    """除虫。body: { user_id, plot_index } 或 { user_id, plot_index: "all" }"""
    data, payload_err = parse_json_payload()
    if payload_err:
        return payload_err
    uid, auth_err = resolve_actor_user_id(data)
    if auth_err:
        return auth_err

    plot_index = data.get("plot_index")
    request_id = data.get("request_id")

    log_action("garden_remove_pest", user_id=uid, request_id=request_id, plot_index=plot_index)

    if plot_index == "all" or plot_index is None:
        result = remove_pest_all(uid)
    else:
        try:
            plot_index = int(plot_index)
        except (TypeError, ValueError):
            return error("INVALID", "Invalid plot_index", 400)
        result = remove_pest(uid, plot_index)

    if not result.get("success"):
        return error(result.get("code", "REMOVE_PEST_FAILED"), result.get("message", ""), 400)
    return success(**result)


# ── POST /api/garden/remove-dead — 清除枯死 ──

@garden_bp.route("/api/garden/remove-dead", methods=["POST"])
def garden_remove_dead():
    """清除枯死灵植。body: { user_id, plot_index } 或 { user_id, plot_index: "all" }"""
    data, payload_err = parse_json_payload()
    if payload_err:
        return payload_err
    uid, auth_err = resolve_actor_user_id(data)
    if auth_err:
        return auth_err

    plot_index = data.get("plot_index")
    request_id = data.get("request_id")

    log_action("garden_remove_dead", user_id=uid, request_id=request_id, plot_index=plot_index)

    if plot_index == "all" or plot_index is None:
        result = remove_dead_all(uid)
    else:
        try:
            plot_index = int(plot_index)
        except (TypeError, ValueError):
            return error("INVALID", "Invalid plot_index", 400)
        result = remove_dead(uid, plot_index)

    if not result.get("success"):
        return error(result.get("code", "REMOVE_DEAD_FAILED"), result.get("message", ""), 400)
    return success(**result)
