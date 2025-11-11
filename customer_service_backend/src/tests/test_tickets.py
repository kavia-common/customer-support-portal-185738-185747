from fastapi.testclient import TestClient


def test_create_ticket_anonymous_or_with_creator(client: TestClient):
    # anonymous create (no creator_id)
    r = client.post("/tickets", json={"title": "Help needed", "description": "It broke"})
    assert r.status_code == 200
    t = r.json()
    assert t["title"] == "Help needed"
    assert t["status"] == "open"

    # create with creator_id (register to get id)
    reg = client.post("/auth/register", json={"email": "c@example.com"}).json()
    r2 = client.post("/tickets", json={"title": "Mine", "creator_id": reg["user_id"]})
    assert r2.status_code == 200
    assert r2.json()["creator_id"] == reg["user_id"]


def test_list_get_update_public(client: TestClient):
    c = client.post("/tickets", json={"title": "A"}).json()
    tid = c["id"]

    # List tickets is public
    r_list = client.get("/tickets")
    assert r_list.status_code == 200
    assert isinstance(r_list.json(), list)

    # Get ticket is public
    r_get = client.get(f"/tickets/{tid}")
    assert r_get.status_code == 200

    # Update ticket is public
    r_put = client.put(f"/tickets/{tid}", json={"status": "closed"})
    assert r_put.status_code == 200
    assert r_put.json()["status"] == "closed"
