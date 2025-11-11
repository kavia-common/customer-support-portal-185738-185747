from fastapi.testclient import TestClient


def test_register_returns_placeholder_token(client: TestClient):
    res = client.post("/auth/register", json={"email": "newuser@example.com", "full_name": "New User"})
    assert res.status_code == 200, res.text
    data = res.json()
    # returns placeholder token for compatibility
    assert "access_token" in data
    assert data.get("token_type") in ("none", "bearer")
    assert "user_id" in data


def test_register_idempotent(client: TestClient):
    payload = {"email": "dup@example.com"}
    r1 = client.post("/auth/register", json=payload)
    assert r1.status_code == 200
    r2 = client.post("/auth/register", json=payload)
    assert r2.status_code == 200
    assert r2.json().get("message") in ("already_registered", "registered")


def test_login_creates_user_without_password(client: TestClient):
    email = "loginuser@example.com"
    r2 = client.post("/auth/login", params={"username": email})
    assert r2.status_code == 200
    assert r2.json().get("access_token")


def test_auth_me_is_public(client: TestClient):
    r = client.get("/auth/me")
    assert r.status_code == 200
    me = r.json()
    # Public/anonymous profile
    assert me.get("note") == "authentication disabled; anonymous access"
