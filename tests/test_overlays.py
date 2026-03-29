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
    assert data["type"] == "hunt"
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
    assert r.status_code == 204
    ids = [o["id"] for o in client.get("/api/overlays").get_json()]
    assert o1["id"] not in ids
    assert o2["id"] in ids


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


def test_new_hunt_not_added_to_existing_overlays(client, overlay):
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
    assert hunt_id not in hunt_ids


def test_delete_hunt_removes_from_hunt_overlays_only(client, overlay):
    hunt = client.post(
        "/api/hunts",
        json={
            "pokemon": "bulbasaur",
            "displayName": "Bulbasaur",
            "spriteUrl": None,
            "game": None,
        },
    ).get_json()
    stats_ov = client.post(
        "/api/overlays", json={"name": "mystats", "type": "stats"}
    ).get_json()
    client.put(
        f"/api/overlays/{overlay['id']}",
        json={"hunts": [{"huntId": hunt["id"], "visible": True}]},
    )
    client.delete(f"/api/hunts/{hunt['id']}")
    overlays = client.get("/api/overlays").get_json()
    hunt_ov = next(o for o in overlays if o["id"] == overlay["id"])
    stats = next(o for o in overlays if o["id"] == stats_ov["id"])
    assert not any(h["huntId"] == hunt["id"] for h in hunt_ov["hunts"])
    assert "hunts" not in stats


def test_overlay_route_hunt_suffix(client, overlay):
    r = client.get(f"/overlay/{overlay['name']}-hunt")
    assert r.status_code == 200


def test_overlay_route_stats_suffix(client):
    o = client.post(
        "/api/overlays", json={"name": "mystats", "type": "stats"}
    ).get_json()
    r = client.get(f"/overlay/{o['name']}-stats")
    assert r.status_code == 200


def test_overlay_route_suffix_name_conflict(client):
    client.post("/api/overlays", json={"name": "test", "type": "hunt"})
    client.post("/api/overlays", json={"name": "test", "type": "stats"})
    r_hunt = client.get("/overlay/test-hunt")
    r_stats = client.get("/overlay/test-stats")
    assert r_hunt.status_code == 200
    assert r_stats.status_code == 200


def test_overlay_route_not_found(client):
    r = client.get("/overlay/doesntexist")
    assert r.status_code == 404


def test_add_stats_overlay(client):
    r = client.post("/api/overlays", json={"name": "my-stats", "type": "stats"})
    assert r.status_code == 201
    data = r.get_json()
    assert data["type"] == "stats"
    assert data["name"] == "my-stats"
    assert data["elements"]["totalCompleted"] is True
    assert data["elements"]["breakdown"] == "completed"
    assert data["game"] is None


def test_add_overlay_invalid_type(client):
    r = client.post("/api/overlays", json={"name": "bad", "type": "invalid"})
    assert r.status_code == 400


def test_update_stats_overlay_elements(client):
    o = client.post("/api/overlays", json={"name": "stats", "type": "stats"}).get_json()
    r = client.put(
        f"/api/overlays/{o['id']}",
        json={"elements": {"totalCompleted": False, "breakdown": "active"}},
    )
    assert r.status_code == 200
    data = r.get_json()
    assert data["elements"]["totalCompleted"] is False
    assert data["elements"]["breakdown"] == "active"


def test_update_stats_overlay_game(client):
    o = client.post("/api/overlays", json={"name": "stats", "type": "stats"}).get_json()
    r = client.put(f"/api/overlays/{o['id']}", json={"game": "Red / Blue"})
    assert r.status_code == 200
    assert r.get_json()["game"] == "Red / Blue"


def test_migrate_overlays_adds_type(client):
    # Create an overlay with no type direcly in store
    import json

    import store
    from app import migrate_overlays

    overlay = {
        "id": "test-id",
        "name": "old",
        "elements": {"sprite": None, "name": True, "count": True, "odds": False},
        "hunts": [],
    }
    store.save_overlays([overlay])
    migrate_overlays()
    overlays = store.load_overlays()
    assert overlays[0]["type"] == "hunt"


def test_can_delete_last_overlay(client, overlay):
    r = client.delete(f"/api/overlays/{overlay['id']}")
    assert r.status_code == 204
    assert client.get("/api/overlays").get_json() == []


def test_overlay_bare_path_not_found(client):
    r = client.get("/overlay")
    assert r.status_code == 404


def test_update_overlay_empty_name(client, overlay):
    r = client.put(f"/api/overlays/{overlay['id']}", json={"name": "  "})
    assert r.status_code == 400
    assert r.get_json()["error"] == "name is required"


def test_update_overlay_elements_not_dict(client, overlay):
    r = client.put(f"/api/overlays/{overlay['id']}", json={"elements": "bad"})
    assert r.status_code == 400
    assert r.get_json()["error"] == "elements must be an object"


def test_update_hunt_overlay_elements_missing_key(client, overlay):
    r = client.put(
        f"/api/overlays/{overlay['id']}",
        json={"elements": {"sprite": True, "name": True, "count": True}},
    )
    assert r.status_code == 400
    assert (
        r.get_json()["error"]
        == "hunt overlay elements must contain exactly: ['count', 'name', 'odds', 'sprite']"
    )


def test_update_hunt_overlay_elements_extra_key(client, overlay):
    r = client.put(
        f"/api/overlays/{overlay['id']}",
        json={
            "elements": {
                "sprite": True,
                "name": True,
                "count": True,
                "odds": False,
                "extra": True,
            }
        },
    )
    assert r.status_code == 400
    assert (
        r.get_json()["error"]
        == "hunt overlay elements must contain exactly: ['count', 'name', 'odds', 'sprite']"
    )


def test_update_hunt_overlay_elements_wrong_type(client, overlay):
    r = client.put(
        f"/api/overlays/{overlay['id']}",
        json={"elements": {"sprite": True, "name": True, "count": True, "odds": "yes"}},
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "hunt overlay elements must all be booleans"


def test_update_stats_overlay_total_completed_wrong_type(client):
    o = client.post(
        "/api/overlays", json={"name": "stats-val", "type": "stats"}
    ).get_json()
    r = client.put(
        f"/api/overlays/{o['id']}",
        json={"elements": {"totalCompleted": "yes", "breakdown": "completed"}},
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "totalCompleted must be a boolean"


def test_update_stats_overlay_breakdown_invalid_value(client):
    o = client.post(
        "/api/overlays", json={"name": "stats-val2", "type": "stats"}
    ).get_json()
    r = client.put(
        f"/api/overlays/{o['id']}",
        json={"elements": {"totalCompleted": True, "breakdown": "invalid"}},
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "breakdown must be 'completed', 'active', or null"


def test_update_overlay_hunts_not_a_list(client, overlay):
    r = client.put(f"/api/overlays/{overlay['id']}", json={"hunts": "bad"})
    assert r.status_code == 400
    assert r.get_json()["error"] == "hunts must be a list"


def test_update_overlay_hunts_invalid_entry(client, overlay):
    r = client.put(
        f"/api/overlays/{overlay['id']}",
        json={"hunts": [{"huntId": "abc", "visible": "yes"}]},
    )
    assert r.status_code == 400
    assert (
        r.get_json()["error"]
        == "each hunt entry must have huntId (string) and visible (boolean)"
    )


def test_update_overlay_game_invalid_type(client, overlay):
    r = client.put(f"/api/overlays/{overlay['id']}", json={"game": 123})
    assert r.status_code == 400
    assert r.get_json()["error"] == "game must be a string or null"


def test_new_overlay_starts_with_empty_hunts(client, hunt):
    r = client.post("/api/overlays", json={"name": "new-overlay"})
    assert r.status_code == 201
    assert r.get_json()["hunts"] == []
