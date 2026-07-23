import pytest

from app import create_app


@pytest.fixture()
def app():
    """A fresh app per test, backed by an in-memory SQLite DB so tests
    never touch the real MySQL database."""
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret",
        }
    )
    yield application


@pytest.fixture()
def client(app):
    return app.test_client()
