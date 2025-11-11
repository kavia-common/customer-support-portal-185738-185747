from fastapi.testclient import TestClient


def _me(client: TestClient, token: str):
    return client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).json()


def test_customer_create_own_ticket(client: TestClient):
    token = client.post("/auth/register", json={"email": "c1@example.com", "password": "secret12"}).json()["access_token"]
    me = _me(client, token)
    payload = {"title": "Help needed", "description": "It broke", "creator_id": me["id"]}
    r = client.post("/tickets", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    t = r.json()
    assert t["title"] == "Help needed"
    assert t["creator_id"] == me["id"]
    assert t["status"] == "open"


def test_customer_cannot_create_for_other(client: TestClient):
    t1 = client.post("/auth/register", json={"email": "c2@example.com", "password": "secret12"}).json()["access_token"]
    t2 = client.post("/auth/register", json={"email": "c3@example.com", "password": "secret12"}).json()["access_token"]
    me2 = _me(client, t2)
    payload = {"title": "Not allowed", "creator_id": me2["id"]}
    r = client.post("/tickets", json=payload, headers={"Authorization": f"Bearer {t1}"})
    assert r.status_code == 403


def test_list_tickets_customer_sees_only_own(client: TestClient):
    t1 = client.post("/auth/register", json={"email": "list1@example.com", "password": "secret12"}).json()["access_token"]
    t2 = client.post("/auth/register", json={"email": "list2@example.com", "password": "secret12"}).json()["access_token"]
    me1 = _me(client, t1)
    me2 = _me(client, t2)

    # create one ticket for each
    client.post("/tickets", json={"title": "A", "creator_id": me1["id"]}, headers={"Authorization": f"Bearer {t1}"})
    client.post("/tickets", json={"title": "B", "creator_id": me2["id"]}, headers={"Authorization": f"Bearer {t2}"})

    r1 = client.get("/tickets", headers={"Authorization": f"Bearer {t1}"})
    assert r1.status_code == 200
    l1 = r1.json()
    assert all(t["creator_id"] == me1["id"] for t in l1)

    r2 = client.get("/tickets", headers={"Authorization": f"Bearer {t2}"})
    l2 = r2.json()
    assert all(t["creator_id"] == me2["id"] for t in l2)


def test_agent_sees_all_tickets(client: TestClient):
    agent = client.post("/auth/register", json={"email": "agent.tix@example.com", "password": "secret12", "is_agent": True}).json()["access_token"]
    c = client.post("/auth/register", json={"email": "cust.tix@example.com", "password": "secret12"}).json()["access_token"]
    me_c = _me(client, c)
    client.post("/tickets", json={"title": "Customer ticket", "creator_id": me_c["id"]}, headers={"Authorization": f"Bearer {c}"})
    r = client.get("/tickets", headers={"Authorization": f"Bearer {agent}"})
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    assert len(r.json()) >= 1


def test_get_ticket_rbac(client: TestClient):
    cust = client.post("/auth/register", json={"email": "own@example.com", "password": "secret12"}).json()["access_token"]
    other = client.post("/auth/register", json={"email": "other@example.com", "password": "secret12"}).json()["access_token"]
    agent = client.post("/auth/register", json={"email": "agent2@example.com", "password": "secret12", "is_agent": True}).json()["access_token"]
    me = _me(client, cust)

    created = client.post("/tickets", json={"title": "Mine", "creator_id": me["id"]}, headers={"Authorization": f"Bearer {cust}"}).json()
    tid = created["id"]

    # Owner can get
    r_ok = client.get(f"/tickets/{tid}", headers={"Authorization": f"Bearer {cust}"})
    assert r_ok.status_code == 200

    # Other customer cannot
    r_forbid = client.get(f"/tickets/{tid}", headers={"Authorization": f"Bearer {other}"})
    assert r_forbid.status_code == 403

    # Agent can
    r_agent = client.get(f"/tickets/{tid}", headers={"Authorization": f"Bearer {agent}"})
    assert r_agent.status_code == 200


def test_update_ticket_customer_limits_and_agent_privileges(client: TestClient):
    cust = client.post("/auth/register", json={"email": "upd.cust@example.com", "password": "secret12"}).json()["access_token"]
    agent = client.post("/auth/register", json={"email": "upd.agent@example.com", "password": "secret12", "is_agent": True}).json()["access_token"]
    me = _me(client, cust)
    t = client.post("/tickets", json={"title": "Original", "description": "D", "creator_id": me["id"]}, headers={"Authorization": f"Bearer {cust}"}).json()
    tid = t["id"]

    # Customer can change title/description
    r1 = client.put(f"/tickets/{tid}", json={"title": "Changed by customer", "description": "New"}, headers={"Authorization": f"Bearer {cust}"})
    assert r1.status_code == 200
    assert r1.json()["title"] == "Changed by customer"

    # Customer cannot change status/assignee
    r2 = client.put(f"/tickets/{tid}", json={"status": "closed"}, headers={"Authorization": f"Bearer {cust}"})
    assert r2.status_code == 403

    # Agent can change status/assignee
    r3 = client.put(f"/tickets/{tid}", json={"status": "closed"}, headers={"Authorization": f"Bearer {agent}"})
    assert r3.status_code == 200
    assert r3.json()["status"] == "closed"
