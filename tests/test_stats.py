import json


def test_stats_empty(client):
    r = client.get("/api/stats")
    assert r.status_code == 200
    data = r.get_json()
    assert data["totalCompleted"] == 0
    assert data["totalActive"] == 0
    assert data["byGame"] == {}


def test_stats_counts(client):
    client.post("/api/overlays", json={"name": "main"})
    client.post(
        "/api/hunts",
        json={
            "pokemon": "bulbasaur",
            "displayName": "Bulbasaur",
            "spriteUrl": None,
            "game": "Red / Blue",
        },
    )
    client.post(
        "/api/hunts",
        json={
            "pokemon": "charmander",
            "displayName": "Charmander",
            "spriteUrl": None,
            "game": "Red / Blue",
        },
    )
    client.post(
        "/api/hunts",
        json={
            "pokemon": "squirtle",
            "displayName": "Squirtle",
            "spriteUrl": None,
            "game": None,
        },
    )

    hunts = client.get("/api/hunts?scope=all").get_json()
    client.post(f"/api/hunts/{hunts[0]['id']}/complete", json={})

    r = client.get("/api/stats")
    data = r.get_json()
    assert data["totalCompleted"] == 1
    assert data["totalActive"] == 2


def test_stats_by_game(client):
    client.post("/api/overlays", json={"name": "main"})
    client.post(
        "/api/hunts",
        json={
            "pokemon": "bulbasaur",
            "displayName": "Bulbasaur",
            "spriteUrl": None,
            "game": "Red / Blue",
        },
    )
    client.post(
        "/api/hunts",
        json={
            "pokemon": "squirtle",
            "displayName": "Squirtle",
            "spriteUrl": None,
            "game": None,
        },
    )

    hunts = client.get("/api/hunts?scope=all").get_json()
    client.post(f"/api/hunts/{hunts[0]['id']}/complete", json={})

    r = client.get("/api/stats")
    data = r.get_json()
    assert data["byGame"]["Red / Blue"]["completed"] == 1
    assert data["byGame"]["Red / Blue"]["active"] == 0
    assert data["byGame"]["None"]["completed"] == 0
    assert data["byGame"]["None"]["active"] == 1
