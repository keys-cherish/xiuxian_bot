"""Lightweight metrics/event logging for guardrails and reports."""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, Optional

from core.database.connection import execute

logger = logging.getLogger("core.metrics")


def log_event(
    event: str,
    *,
    user_id: str = "",
    success: bool = True,
    request_id: Optional[str] = None,
    reason: Optional[str] = None,
    rank: Optional[int] = None,
    meta: Optional[Dict[str, Any]] = None,
    ts: Optional[int] = None,
) -> None:
    if not event:
        return
    ts = int(time.time()) if ts is None else int(ts)
    try:
        payload = json.dumps(meta or {}, ensure_ascii=False)
    except Exception:
        payload = "{}"
    try:
        execute(
            """INSERT INTO event_logs (ts, user_id, event, success, rank, request_id, reason, meta_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                ts,
                str(user_id or ""),
                str(event),
                1 if success else 0,
                int(rank) if rank is not None else None,
                request_id,
                reason,
                payload,
            ),
        )
    except Exception as exc:
        logger.warning(
            "log_event_failed event=%s user_id=%s error=%s",
            event,
            user_id,
            type(exc).__name__,
        )


def log_economy_ledger(
    *,
    user_id: str,
    module: str,
    action: str,
    delta_copper: int = 0,
    delta_gold: int = 0,
    delta_exp: int = 0,
    delta_stamina: int = 0,
    currency: Optional[str] = None,
    item_id: Optional[str] = None,
    qty: Optional[int] = None,
    shown_price: Optional[int] = None,
    actual_price: Optional[int] = None,
    success: bool = True,
    reason: Optional[str] = None,
    request_id: Optional[str] = None,
    rank: Optional[int] = None,
    meta: Optional[Dict[str, Any]] = None,
    ts: Optional[int] = None,
) -> None:
    ts = int(time.time()) if ts is None else int(ts)
    try:
        payload = json.dumps(meta or {}, ensure_ascii=False)
    except Exception:
        payload = "{}"
    try:
        execute(
            """INSERT INTO economy_ledger (
                   ts, user_id, rank, module, action, currency, item_id, qty,
                   delta_copper, delta_gold, delta_exp, delta_stamina,
                   shown_price, actual_price, success, reason, request_id, meta_json
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                ts,
                str(user_id or ""),
                int(rank) if rank is not None else None,
                str(module or ""),
                str(action or ""),
                currency,
                item_id,
                int(qty) if qty is not None else None,
                int(delta_copper or 0),
                int(delta_gold or 0),
                int(delta_exp or 0),
                int(delta_stamina or 0),
                int(shown_price) if shown_price is not None else None,
                int(actual_price) if actual_price is not None else None,
                1 if success else 0,
                reason,
                request_id,
                payload,
            ),
        )
    except Exception as exc:
        logger.warning(
            "log_ledger_failed module=%s action=%s user_id=%s error=%s",
            module,
            action,
            user_id,
            type(exc).__name__,
        )


def log_guardrail_alert(
    *,
    report_date: str,
    metric: str,
    value: float,
    lower: Optional[float] = None,
    upper: Optional[float] = None,
    level: str = "warn",
    detail: Optional[Dict[str, Any]] = None,
    ts: Optional[int] = None,
) -> None:
    ts = int(time.time()) if ts is None else int(ts)
    try:
        payload = json.dumps(detail or {}, ensure_ascii=False)
    except Exception:
        payload = "{}"
    try:
        execute(
            """INSERT INTO guardrail_alerts
               (report_date, metric, value, lower_bound, upper_bound, level, detail_json, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                report_date,
                metric,
                float(value),
                float(lower) if lower is not None else None,
                float(upper) if upper is not None else None,
                str(level),
                payload,
                ts,
            ),
        )
    except Exception as exc:
        logger.warning(
            "log_guardrail_alert_failed metric=%s error=%s",
            metric,
            type(exc).__name__,
        )
