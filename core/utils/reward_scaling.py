"""Reward scaling helpers."""

from __future__ import annotations

from typing import Any, Dict, List

from core.config import config


DEFAULT_RANK_TIERS: List[Dict[str, Any]] = [
    {"max_rank": 5, "mult": 1.0},
    {"max_rank": 10, "mult": 1.1},
    {"max_rank": 15, "mult": 1.2},
    {"max_rank": 20, "mult": 1.35},
    {"max_rank": 25, "mult": 1.5},
    {"max_rank": 30, "mult": 1.65},
]
DEFAULT_RANK_CAP = 1.8


def _coerce_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def rank_scale(rank: int) -> float:
    tiers = config.get_nested("balance", "rank_reward_tiers", default=None)
    cap = config.get_nested("balance", "rank_reward_cap", default=DEFAULT_RANK_CAP)
    if not isinstance(tiers, list) or not tiers:
        tiers = DEFAULT_RANK_TIERS
    r = int(rank or 1)
    mult = tiers[-1].get("mult", 1.0) if tiers else 1.0
    for tier in tiers:
        try:
            if r <= int(tier.get("max_rank", 0) or 0):
                mult = tier.get("mult", 1.0)
                break
        except (TypeError, ValueError):
            continue
    mult = _coerce_float(mult, 1.0)
    cap_val = None if cap is None else _coerce_float(cap, DEFAULT_RANK_CAP)
    if cap_val is not None:
        mult = min(mult, cap_val)
    return max(0.1, float(mult))
