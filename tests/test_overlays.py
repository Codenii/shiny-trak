def test_get_overlays_empty(client):
    r = client.get("/api/overlays")
    assert r.status_code == 200
    assert r.get_json() == []


def test_add_overlay(client):
    r = client.post("/api/overlays", json={"name": "main"})
    assert r.status_code == 201
    data = r.get_json()
    assert data["name"] == "main"
    assert "id" in data
    assert data["elements"] == {
        "sprite": True,
        "name": True,
        "count": True,
        "odds": False,
    }


def test_add_overlay_empty_name(client):
    r = client.post("/api/overlays", json={"name": ""})
    assert r.status_code == 400


def test_add_overlay_appears_in_list(client, overlay):
    r = client.get("/api/overlays")
    ids = [o["id"] for o in r.get_json()]
    assert overlay["id"] in ids


def test_delete_overlay(client):
    o1 = client.post("/api/overlays", json={"name": "first"}).get_json()
    o2 = client.post("/api/overlays", json={"name": "second"}).get_json()
    r = client.delete(f"/api/overlays/{o1['id']}")
    assert r.status_code == 200
    ids = [o["id"] for o in client.get("/api/overlays").get_json()]
    assert o1["id"] not in ids
    assert o2["id"] in ids


def test_cannot_delete_last_overlay(client, overlay):
    r = client.delete(f"/api/overlays/{overlay['id']}")
    assert r.status_code == 400


def test_update_overlay_name(client, overlay):
    r = client.put(f"/api/overlays/{overlay['id']}", json={"name": "renamed"})
    assert r.status_code == 200
    assert r.get_json()["name"] == "renamed"


def test_update_overlay_elements(client, overlay):
    r = client.put(
        f"/api/overlays/{overlay['id']}",
        json={"elements": {"sprite": False, "name": True, "count": True, "odds": True}},
    )
    assert r.status_code == 200
    data = r.get_json()
    assert data["elements"]["sprite"] is False
    assert data["elements"]["odds"] is True


def test_update_overlay_hunt_visibility(client, overlay, hunt):
    updated_hunts = [{"huntId": hunt["id"], "visible": False}]
    r = client.put(f"/api/overlays/{overlay['id']}", json={"hunts": updated_hunts})
    assert r.status_code == 200
    match = next(h for h in r.get_json()["hunts"] if h["huntId"] == hunt["id"])
    assert match["visible"] is False


def test_new_hunt_added_to_existing_overlays(client, overlay):
    r = client.post(
        "/api/hunts",
        json={
            "pokemon": "bulbasaur",
            "displayName": "Bulbasaur",
            "spriteUrl": None,
            "game": None,
        },
    )
    hunt_id = r.get_json()["id"]
    overlays = client.get("/api/overlays").get_json()
    hunt_ids = [h["huntId"] for h in overlays[0]["hunts"]]
    assert hunt_id in hunt_ids


def test_overlay_route(client, overlay):
    r = client.get(f"/overlay/{overlay['name']}")
    assert r.status_code == 200


def test_overlay_route_not_found(client):
    r = client.get("/overlay/doesntexist")
    assert r.status_code == 404
