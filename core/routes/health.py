"""健康检查路由。"""

import time

from flask import Blueprint

from core.routes._helpers import success
from core.game.mechanics import get_daily_element
from core.database.connection import fetch_schema_version
from core.config import config
from core.utils.timeutil import format_utc_iso

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health_check():
    return success(
        status="healthy",
        timestamp=time.time(),
        daily_element=get_daily_element(),
    )


@health_bp.route("/api/health", methods=["GET"])
def api_health_check():
    """Health endpoint for bot/ops checks."""
    git_sha = None
    try:
        import subprocess
        git_sha = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=config.project_root,
            stderr=subprocess.DEVNULL,
        ).decode().strip()
    except Exception:
        pass

    return success(
        ok=True,
        schema_version=fetch_schema_version(),
        git_sha=git_sha,
        time=format_utc_iso(),
    )
