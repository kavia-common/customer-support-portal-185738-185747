from fastapi.testclient import TestClient
from src.api.main import app


def test_health_ok():
    client = TestClient(app)
    r = client.get("/")
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, dict)
    assert body.get("message") == "Healthy"
