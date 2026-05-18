from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_200_and_ok():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "version" in body
    assert "env" in body
