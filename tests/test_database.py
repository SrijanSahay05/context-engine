import os

import pytest
from sqlalchemy import text
from sqlalchemy.engine import make_url

from db.session import DatabaseSessionManager


def test_database_connection() -> None:
    database_url = os.environ.get("TEST_DATABASE_URL")
    if database_url is None:
        pytest.skip("Set TEST_DATABASE_URL to run the database integration check")

    manager = DatabaseSessionManager(make_url(database_url))
    try:
        with manager.session() as session:
            assert session.scalar(text("SELECT 1")) == 1
            assert session.scalar(text(
                "SELECT EXISTS ("
                "SELECT 1 FROM pg_extension WHERE extname = 'vector'"
                ")"
            ))
            assert session.scalar(text("SELECT '[1,2,3]'::vector::text")) == "[1,2,3]"
    finally:
        manager.dispose()
