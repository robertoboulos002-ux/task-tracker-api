import os

import pytest
from fastapi.testclient import TestClient

from app import storage
from app.main import app


@pytest.fixture(autouse=True)
def _reset_storage():
    def _reset():
        if hasattr(storage, "_reset"):
            storage._reset()
        else:
            data_file = getattr(storage, "DATA_FILE", None)
            if data_file and os.path.exists(data_file):
                os.remove(data_file)

    _reset()
    yield
    _reset()


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def created_task(client):
    response = client.post("/tasks", json={"title": "fixture task"})
    assert response.status_code == 201
    return response.json()
