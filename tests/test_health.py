"""
Tests for the /health endpoint.

Uses FastAPI's TestClient (built on httpx) to send real requests to the
app instance without needing a running uvicorn server.
"""

from datetime import datetime

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_200():
    """The /health endpoint should respond with HTTP 200."""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_returns_status_ok():
    """The response body should contain status: ok."""
    response = client.get("/health")
    body = response.json()
    assert body["status"] == "ok"


def test_health_returns_valid_iso_timestamp():
    """The timestamp field should be present and a valid ISO-8601 string."""
    response = client.get("/health")
    body = response.json()
    assert "timestamp" in body

    # This will raise a ValueError if the timestamp is not valid ISO-8601
    parsed = datetime.fromisoformat(body["timestamp"])
    assert isinstance(parsed, datetime)


def test_health_response_shape():
    """The response should contain exactly the two expected fields."""
    response = client.get("/health")
    body = response.json()
    assert set(body.keys()) == {"status", "timestamp"}
