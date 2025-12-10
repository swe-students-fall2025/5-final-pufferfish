"""Basic tests for the Flask application."""

import pytest
from app import create_app


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app = create_app()
    app.config["TESTING"] = True
    app.config["MONGO_URI"] = "mongomock://localhost"

    with app.test_client() as c:
        yield c


def test_index_route(c):
    """Test the index route."""
    response = c.get("/")
    assert response.status_code == 200
