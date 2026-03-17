"""统一时间工具。

所有内部计算使用 UTC 时间戳，对外展示按服务器时区（默认 UTC+8）转换。
"""

import datetime
import time
from typing import Optional


def utc_now() -> datetime.datetime:
    """返回当前 UTC 时间（带时区信息）。"""
    return datetime.datetime.now(datetime.timezone.utc)


def utc_timestamp() -> int:
    """返回当前 UTC 时间戳（整数秒）。"""
    return int(time.time())


def today_utc() -> str:
    """返回今天的 UTC 日期字符串 (YYYY-MM-DD)。"""
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")


def today_local(tz_offset_hours: int = 8) -> str:
    """返回今天的本地日期字符串（默认 UTC+8）。"""
    tz = datetime.timezone(datetime.timedelta(hours=tz_offset_hours))
    return datetime.datetime.now(tz).strftime("%Y-%m-%d")


def midnight_timestamp(tz_offset_hours: int = 8) -> int:
    """返回今天午夜的时间戳（用于每日重置判定）。"""
    tz = datetime.timezone(datetime.timedelta(hours=tz_offset_hours))
    now = datetime.datetime.now(tz)
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return int(midnight.timestamp())


def local_day_key(now: Optional[int] = None, tz_offset_hours: int = 8) -> int:
    """返回本地日序号（默认按北京时间 00:00 切日）。"""
    now = int(time.time()) if now is None else int(now)
    return int((now + int(tz_offset_hours) * 3600) // 86400)


def format_utc_iso() -> str:
    """返回 UTC ISO 8601 格式字符串（用于 API 响应）。"""
    return utc_now().replace(microsecond=0).isoformat().replace("+00:00", "Z")
