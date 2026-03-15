import app as app_module


def test_get_hunts_empty(client):
    r = client.get("/api/hunts")
    assert r.status_code == 200
    assert r.get_json() == []


def test_add_hunt(client, overlay):
    r = client.post(
        "/api/hunts",
        json={
            "pokemon": "pikachu",
            "displayName": "Pikachu",
            "spriteUrl": "https://example.com/pikachu.png",
            "game": None,
        },
    )
    assert r.status_code == 201
    data = r.get_json()
    assert data["pokemon"] == "pikachu"
    assert data["displayName"] == "Pikachu"
    assert data["count"] == 0
    assert data["status"] == "active"
    assert "id" in data


def test_add_hunt_appears_in_list(client, hunt):
    r = client.get("/api/hunts")
    assert r.status_code == 200
    ids = [h["id"] for h in r.get_json()]
    assert hunt["id"] in ids


def test_update_hunt(client, hunt):
    r = client.put(f"/api/hunts/{hunt['id']}", json={"displayName": "Pika"})
    assert r.status_code == 200
    assert r.get_json()["displayName"] == "Pika"


def test_update_hunt_not_found(client):
    r = client.put("/api/hunts/nonexistent", json={"displayName": "X"})
    assert r.status_code == 404


def test_delete_hunt(client, hunt):
    r = client.delete(f"/api/hunts/{hunt['id']}")
    assert r.status_code == 200
    ids = [h["id"] for h in client.get("/api/hunts").get_json()]
    assert hunt["id"] not in ids


def test_increment(client, hunt):
    r = client.post(f"/api/hunts/{hunt['id']}/increment")
    assert r.status_code == 200
    assert r.get_json()["count"] == 1


def test_decrement(client, hunt):
    client.post(f"/api/hunts/{hunt['id']}/increment")
    client.post(f"/api/hunts/{hunt['id']}/increment")
    r = client.post(f"/api/hunts/{hunt['id']}/decrement")
    assert r.status_code == 200
    assert r.get_json()["count"] == 1


def test_decrement_floor_zero(client, hunt):
    r = client.post(f"/api/hunts/{hunt['id']}/decrement")
    assert r.status_code == 200
    assert r.get_json()["count"] == 0


def test_reset(client, hunt):
    client.post(f"/api/hunts/{hunt['id']}/increment")
    client.post(f"/api/hunts/{hunt['id']}/increment")
    r = client.post(f"/api/hunts/{hunt['id']}/reset")
    assert r.status_code == 200
    assert r.get_json()["count"] == 0


def test_complete_hunt(client, hunt):
    r = client.post(f"/api/hunts/{hunt['id']}/complete", json={"notes": "Got it!"})
    assert r.status_code == 200
    data = r.get_json()
    assert data["status"] == "completed"
    assert data["notes"] == "Got it!"
    assert data["endDate"] is not None


def test_set_count(client, hunt):
    r = client.put(f"/api/hunts/{hunt['id']}", json={"count": 500})
    assert r.status_code == 200
    assert r.get_json()["count"] == 500


def test_set_count_negative_clamps_to_zero(client, hunt):
    r = client.put(f"/api/hunts/{hunt['id']}", json={"count": -10})
    assert r.status_code == 200
    assert r.get_json()["count"] == 0


def test_increment_not_found(client):
    r = client.post("/api/hunts/nonexistent/increment")
    assert r.status_code == 404


def test_encounter_rate(client, hunt):
    r = client.put(f"/api/hunts/{hunt['id']}", json={"encounterRate": 4096})
    assert r.status_code == 200
    assert r.get_json()["encounterRate"] == 4096


def test_get_hunts_scope_active(client, hunt):
    client.post(f"/api/hunts/{hunt['id']}/complete", json={})
    resp = client.get("/api/hunts?scope=active")
    assert not any(h["id"] == hunt["id"] for h in resp.get_json())


def test_get_hunts_scope_completed(client, hunt):
    client.post(f"/api/hunts/{hunt['id']}/complete", json={})
    resp = client.get("/api/hunts?scope=completed")
    assert any(h["id"] == hunt["id"] for h in resp.get_json())


def test_get_hunts_scope_all(client, hunt):
    client.post(f"/api/hunts/{hunt['id']}/complete", json={})
    resp = client.get("/api/hunts?scope=all")
    assert any(h["id"] == hunt["id"] for h in resp.get_json())


def test_milestone_fires_at_1x(client, hunt, monkeypatch):
    client.put(f"/api/hunts/{hunt['id']}", json={"encounterRate": 3, "count": 2})
    fired = []
    monkeypatch.setattr(app_module, "broadcast_milestone", lambda h: fired.append(h))
    client.post(f"/api/hunts/{hunt['id']}/increment")
    assert len(fired) == 1
    assert fired[0]["count"] == 3


def test_milestone_fires_at_2x(client, hunt, monkeypatch):
    client.put(f"/api/hunts/{hunt['id']}", json={"encounterRate": 3, "count": 5})
    fired = []
    monkeypatch.setattr(app_module, "broadcast_milestone", lambda h: fired.append(h))
    client.post(f"/api/hunts/{hunt['id']}/increment")
    assert len(fired) == 1
    assert fired[0]["count"] == 6


def test_milestone_not_at_non_multiple(client, hunt, monkeypatch):
    client.put(f"/api/hunts/{hunt['id']}", json={"encounterRate": 3, "count": 3})
    fired = []
    monkeypatch.setattr(app_module, "broadcast_milestone", lambda h: fired.append(h))
    client.post(f"/api/hunts/{hunt['id']}/increment")
    assert len(fired) == 0


def test_milestone_no_encounter_rate(client, hunt, monkeypatch):
    fired = []
    monkeypatch.setattr(app_module, "broadcast_milestone", lambda h: fired.append(h))
    client.post(f"/api/hunts/{hunt['id']}/increment")
    assert len(fired) == 0


def test_milestone_disabled_in_settings(client, hunt, monkeypatch):
    client.put(f"/api/hunts/{hunt['id']}", json={"encounterRate": 3, "count": 2})
    client.put("/api/settings", json={"milestone_alerts": False})
    fired = []
    monkeypatch.setattr(app_module, "broadcast_milestone", lambda h: fired.append(h))
    client.post(f"/api/hunts/{hunt['id']}/increment")
    assert len(fired) == 0
