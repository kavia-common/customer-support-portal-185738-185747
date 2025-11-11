from fastapi.testclient import TestClient


def _me(client: TestClient, token: str):
    return client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).json()


def _create_ticket(client: TestClient, token: str):
    me = _me(client, token)
    r = client.post("/tickets", json={"title": "Msg Ticket", "creator_id": me["id"]}, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    return r.json()["id"], me["id"]


def test_customer_can_post_to_own_ticket(client: TestClient):
    cust = client.post("/auth/register", json={"email": "m1@example.com", "password": "secret12"}).json()["access_token"]
    ticket_id, uid = _create_ticket(client, cust)
    payload = {"content": "Hello", "ticket_id": ticket_id, "author_id": uid}
    r = client.post("/messages", json=payload, headers={"Authorization": f"Bearer {cust}"})
    assert r.status_code == 200
    m = r.json()
    assert m["content"] == "Hello"
    assert m["ticket_id"] == ticket_id
    assert m["author_id"] == uid


def test_customer_cannot_post_to_others_ticket(client: TestClient):
    owner = client.post("/auth/register", json={"email": "owner@example.com", "password": "secret12"}).json()["access_token"]
    other = client.post("/auth/register", json={"email": "otherc@example.com", "password": "secret12"}).json()["access_token"]
    tid, owner_id = _create_ticket(client, owner)
    me_other = _me(client, other)
    payload = {"content": "Should fail", "ticket_id": tid, "author_id": me_other["id"]}
    r = client.post("/messages", json=payload, headers={"Authorization": f"Bearer {other}"})
    assert r.status_code == 403


def test_cannot_post_as_another_user(client: TestClient):
    cust = client.post("/auth/register", json={"email": "impersonate@example.com", "password": "secret12"}).json()["access_token"]
    tid, uid = _create_ticket(client, cust)

    # create second user id
    x = client.post("/auth/register", json={"email": "someoneelse@example.com", "password": "secret12"}).json()["access_token"]
    x_me = _me(client, x)

    payload = {"content": "I am not them", "ticket_id": tid, "author_id": x_me["id"]}
    r = client.post("/messages", json=payload, headers={"Authorization": f"Bearer {cust}"})
    assert r.status_code == 403


def test_agent_can_post_and_list_any_ticket(client: TestClient):
    agent = client.post("/auth/register", json={"email": "msg.agent@example.com", "password": "secret12", "is_agent": True}).json()["access_token"]
    cust = client.post("/auth/register", json={"email": "msg.cust@example.com", "password": "secret12"}).json()["access_token"]
    tid, _ = _create_ticket(client, cust)
    me_agent = _me(client, agent)

    # Post as agent to customer's ticket
    r = client.post("/messages", json={"content": "Agent reply", "ticket_id": tid, "author_id": me_agent["id"]}, headers={"Authorization": f"Bearer {agent}"})
    assert r.status_code == 200

    # List as agent
    r2 = client.get(f"/messages/ticket/{tid}", headers={"Authorization": f"Bearer {agent}"})
    assert r2.status_code == 200
    assert isinstance(r2.json(), list)
    assert any(m["content"] == "Agent reply" for m in r2.json())


def test_customer_cannot_list_others_messages(client: TestClient):
    c1 = client.post("/auth/register", json={"email": "lm1@example.com", "password": "secret12"}).json()["access_token"]
    c2 = client.post("/auth/register", json={"email": "lm2@example.com", "password": "secret12"}).json()["access_token"]
    tid, _ = _create_ticket(client, c1)
    r = client.get(f"/messages/ticket/{tid}", headers={"Authorization": f"Bearer {c2}"})
    assert r.status_code == 403
