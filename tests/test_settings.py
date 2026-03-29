def test_get_settings_defaults(client):
    r = client.get("/api/settings")
    data = r.get_json()
    assert data["close_behavior"] == "ask"
    assert data["mark_found_behavior"] == "ask"


def test_update_close_behavior(client):
    r = client.put("/api/settings", json={"close_behavior": "minimize"})
    assert r.status_code == 200
    assert r.get_json()["close_behavior"] == "minimize"


def test_update_mark_found_behavior(client):
    r = client.put("/api/settings", json={"mark_found_behavior": "never"})
    assert r.status_code == 200
    assert r.get_json()["mark_found_behavior"] == "never"


def test_update_settings_persists(client):
    client.put("/api/settings", json={"close_behavior": "quit"})
    r = client.get("/api/settings")
    assert r.get_json()["close_behavior"] == "quit"


def test_update_unknown_key_ignored(client):
    r = client.put(
        "/api/settings", json={"close_behavior": "minimize", "hacked": "value"}
    )
    assert r.status_code == 200
    assert "hacked" not in r.get_json()


def test_milestone_alerts_default_true(client):
    r = client.get("/api/settings")
    assert r.get_json()["milestone_alerts"] is True


def test_update_milestone_alerts(client):
    r = client.put("/api/settings", json={"milestone_alerts": False})
    assert r.status_code == 200
    assert r.get_json()["milestone_alerts"] is False


def test_update_settings_invalid_close_behavior(client):
    r = client.put("/api/settings", json={"close_behavior": "explode"})
    assert r.status_code == 400
    assert (
        r.get_json()["error"] == "close_behavior must be 'ask', 'minimize', or 'quit'"
    )


def test_update_settings_invalid_mark_found_behavior(client):
    r = client.put("/api/settings", json={"mark_found_behavior": "always"})
    assert r.status_code == 400
    assert r.get_json()["error"] == "mark_found_behavior must be 'ask' or 'never'"


def test_update_settings_invalid_milestone_alerts(client):
    r = client.put("/api/settings", json={"milestone_alerts": "yes"})
    assert r.status_code == 400
    assert r.get_json()["error"] == "milestone_alerts must be a boolean"
