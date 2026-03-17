import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _run(script_name: str) -> None:
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


@pytest.mark.smoke
@pytest.mark.integration
def test_smoke_social_chat():
    _run("smoke_social_chat.py")
