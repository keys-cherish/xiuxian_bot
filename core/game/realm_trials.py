"""Realm trial definitions."""

from __future__ import annotations

from typing import Dict, Any, Optional

REALM_TRIALS = [
    {"rank": 3, "hunt_target": 3, "secret_target": 0},
    {"rank": 6, "hunt_target": 5, "secret_target": 1},
    {"rank": 10, "hunt_target": 8, "secret_target": 2},
    {"rank": 14, "hunt_target": 10, "secret_target": 3},
    {"rank": 18, "hunt_target": 12, "secret_target": 3},
    {"rank": 22, "hunt_target": 15, "secret_target": 4},
    {"rank": 26, "hunt_target": 18, "secret_target": 4},
    {"rank": 30, "hunt_target": 20, "secret_target": 5},
]


def get_realm_trial_def(rank: int) -> Optional[Dict[str, Any]]:
    current = int(rank or 1)
    for trial in REALM_TRIALS:
        if int(trial.get("rank", 0) or 0) == current:
            return dict(trial)
    return None
