import os
import sys

import pytest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)


@pytest.fixture()
def test_db():
    from core.database.connection import connect_sqlite, create_tables, close_sqlite
    conn = connect_sqlite()
    create_tables()
    yield conn
    close_sqlite()


def create_user(user_id: str, username: str, rank: int = 1, element: str = "火"):
    from core.database.connection import execute
    import time
    execute(
        "INSERT INTO users (user_id, in_game_username, rank, element, created_at, exp, copper, gold) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        (user_id, username, rank, element, int(time.time()), 1000, 1000, 0),
    )
