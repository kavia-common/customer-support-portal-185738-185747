from fastapi.testclient import TestClient


def test_register_returns_token(client: TestClient):
    res = client.post("/auth/register", json={"email": "newuser@example.com", "password": "secret12", "full_name": "New User"})
    assert res.status_code == 200, res.text
    data = res.json()
    assert "access_token" in data
    assert data.get("token_type") == "bearer"


def test_register_duplicate_email(client: TestClient):
    payload = {"email": "dup@example.com", "password": "secret12"}
    r1 = client.post("/auth/register", json=payload)
    assert r1.status_code == 200
    r2 = client.post("/auth/register", json=payload)
    assert r2.status_code in (400, 409)
    # FastAPI raises 400 in implementation
    if r2.status_code == 400:
        assert r2.json().get("detail") == "Email already registered"


def test_login_success_after_register(client: TestClient):
    email = "loginuser@example.com"
    password = "secret12"
    r = client.post("/auth/register", json={"email": email, "password": password})
    assert r.status_code == 200
    # login uses form data username/password
    r2 = client.post("/auth/login", data={"username": email, "password": password}, headers={"Content-Type": "application/x-www-form-urlencoded"})
    assert r2.status_code == 200
    token = r2.json().get("access_token")
    assert token


def test_login_invalid_credentials(client: TestClient):
    r = client.post("/auth/login", data={"username": "nope@example.com", "password": "bad"}, headers={"Content-Type": "application/x-www-form-urlencoded"})
    assert r.status_code == 401


def test_auth_me_returns_current_user(client: TestClient):
    # register and call /auth/me
    reg = client.post("/auth/register", json={"email": "me@example.com", "password": "secret12"})
    token = reg.json()["access_token"]
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    me = r.json()
    assert me["email"] == "me@example.com"
    assert "id" in me
    assert isinstance(me["is_agent"], bool)
