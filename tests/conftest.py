"""Shared pytest fixtures."""

import pytest

from app import create_app


@pytest.fixture
def app(tmp_path):
    """Create an isolated Flask app backed by a temporary SQLite file."""

    application = create_app(
        "development",
        {
            "TESTING": True,
            "DATABASE_URL": str(tmp_path / "test.sqlite3"),
        },
    )
    return application


@pytest.fixture
def client(app):
    """Return a Flask test client for the isolated application."""

    return app.test_client()
