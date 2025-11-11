from fastapi.testclient import TestClient


def test_list_users_public(client: TestClient):
    r = client.get("/users")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_create_and_get_user_public(client: TestClient):
    reg = client.post("/auth/register", json={"email": "u1@example.com"})
    assert reg.status_code == 200
    user_id = reg.json()["user_id"]

    r_ok = client.get(f"/users/{user_id}")
    assert r_ok.status_code == 200
    assert r_ok.json()["email"] == "u1@example.com"


def test_update_user_public(client: TestClient):
    reg = client.post("/auth/register", json={"email": "upd@example.com"})
    user_id = reg.json()["user_id"]
    r = client.put(f"/users/{user_id}", json={"full_name": "Updated Name"})
    assert r.status_code == 200
    assert r.json().get("full_name") == "Updated Name"
