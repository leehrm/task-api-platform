from unittest.mock import patch

from fastapi.testclient import TestClient

from app.config.database import database
from app.lifecycle import lifecycle_state
from app.main import app


client = TestClient(app)


def test_draining_is_not_reported_as_db_failure():
    with patch.object(lifecycle_state, "draining", True):
        response = client.get("/readyz")

    assert response.status_code == 503
    assert response.json()["detail"] == {"status": "draining"}


def test_db_failure_is_reported_as_disconnected():
    with patch.object(database, "check_connection", side_effect=OSError("connection refused")):
        response = client.get("/readyz")

    assert response.status_code == 503
    assert response.json()["detail"]["db"] == "disconnected"


def test_ready_when_not_draining_and_db_is_up():
    with patch.object(database, "check_connection", return_value=None):
        response = client.get("/readyz")

    assert response.status_code == 200
    assert response.json()["db"] == "connected"
