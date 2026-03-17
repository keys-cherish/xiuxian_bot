"""Numeric helpers for display and API payloads."""

from __future__ import annotations


def format_stamina_value(value):
    """Return int when whole, else keep one decimal place for stamina-like values."""
    try:
        val = float(value)
    except (TypeError, ValueError):
        return 0
    if abs(val - int(val)) < 1e-6:
        return int(val)
    return round(val, 1)

