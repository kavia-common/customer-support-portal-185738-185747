from fastapi.testclient import TestClient


def _create_ticket(client: TestClient):
    r = client.post("/tickets", json={"title": "Msg Ticket"})
    assert r.status_code == 200
    return r.json()["id"]


def test_anyone_can_post_and_list_messages(client: TestClient):
    ticket_id = _create_ticket(client)
    payload = {"content": "Hello", "ticket_id": ticket_id}
    r = client.post("/messages", json=payload)
    assert r.status_code == 200
    m = r.json()
    assert m["content"] == "Hello"
    assert m["ticket_id"] == ticket_id

    # List
    r2 = client.get(f"/messages/ticket/{ticket_id}")
    assert r2.status_code == 200
    assert isinstance(r2.json(), list)
    assert any(msg["content"] == "Hello" for msg in r2.json())
