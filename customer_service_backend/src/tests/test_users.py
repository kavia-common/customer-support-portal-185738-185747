from fastapi.testclient import TestClient


def test_list_users_requires_agent(client: TestClient, auth_headers_customer):
    r = client.get("/users", headers=auth_headers_customer)
    assert r.status_code == 403


def test_list_users_as_agent(client: TestClient, auth_headers_agent):
    r = client.get("/users", headers=auth_headers_agent)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_user_self_and_forbidden_other(client: TestClient):
    # create two customers
    t1 = client.post("/auth/register", json={"email": "u1@example.com", "password": "secret12"}).json()["access_token"]
    t2 = client.post("/auth/register", json={"email": "u2@example.com", "password": "secret12"}).json()["access_token"]

    # find user1 id via /auth/me
    me1 = client.get("/auth/me", headers={"Authorization": f"Bearer {t1}"}).json()
    me2 = client.get("/auth/me", headers={"Authorization": f"Bearer {t2}"}).json()

    # user1 can view own profile
    r_ok = client.get(f"/users/{me1['id']}", headers={"Authorization": f"Bearer {t1}"})
    assert r_ok.status_code == 200
    assert r_ok.json()["email"] == "u1@example.com"

    # user1 cannot view user2
    r_forbid = client.get(f"/users/{me2['id']}", headers={"Authorization": f"Bearer {t1}"})
    assert r_forbid.status_code == 403


def test_update_user_self(client: TestClient):
    token = client.post("/auth/register", json={"email": "upd@example.com", "password": "secret12"}).json()["access_token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).json()
    r = client.put(f"/users/{me['id']}", json={"full_name": "Updated Name"}, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json().get("full_name") == "Updated Name"


def test_agent_can_update_other_user(client: TestClient, auth_headers_agent):
    # create a customer
    t = client.post("/auth/register", json={"email": "custx@example.com", "password": "secret12"}).json()["access_token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {t}"}).json()
    # agent updates user
    r = client.put(f"/users/{me['id']}", json={"full_name": "Agent Set"}, headers=auth_headers_agent)
    assert r.status_code == 200
    assert r.json().get("full_name") == "Agent Set"
