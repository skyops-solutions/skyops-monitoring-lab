from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "running"


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


def test_list_items():
    response = client.get("/api/items")
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 5


def test_get_item_valid():
    response = client.get("/api/items/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1


def test_get_item_not_found():
    response = client.get("/api/items/999")
    assert response.status_code == 404


def test_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert b"http_request_duration_seconds" in response.content
