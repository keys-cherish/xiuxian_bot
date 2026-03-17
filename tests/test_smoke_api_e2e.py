import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _run(script_name: str) -> subprocess.CompletedProcess:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script_name)],
        cwd=str(ROOT),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
    )
    if proc.returncode != 0:
        raise AssertionError(
            f"{script_name} failed\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )
    return proc


@pytest.mark.smoke
@pytest.mark.integration
def test_smoke_api_e2e():
    proc = _run("smoke_api_e2e.py")
    output = proc.stdout or ""
    for checkpoint in (
        "CHECKPOINT:register_ok",
        "CHECKPOINT:shop_buy_ok",
        "CHECKPOINT:secret_realm_turn_action_ok",
        "CHECKPOINT:alchemy_brew_ok",
        "CHECKPOINT:gacha_pull_ok",
        "CHECKPOINT:resource_convert_ok",
        "CHECKPOINT:pvp_challenge_ok",
        "CHECKPOINT:smoke_complete",
    ):
        assert checkpoint in output
