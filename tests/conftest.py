import pytest
import store


@pytest.fixture(autouse=True)
def isolate_data(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(store, "DATA_FILE", str(tmp_path / "hunts.json"))
    monkeypatch.setattr(store, "OVERLAYS_FILE", str(tmp_path / "overlays.json"))
    monkeypatch.setattr(store, "SETTINGS_FILE", str(tmp_path / "settings.json"))
    monkeypatch.setattr(store, "_pokemon_list_cache", None)
    store._game_pokemon_cache.clear()


@pytest.fixture
def client():
    from app import app

    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


@pytest.fixture
def overlay(client):
    r = client.post("/api/overlays", json={"name": "main"})
    return r.get_json()


@pytest.fixture
def hunt(client, overlay):
    r = client.post(
        "/api/hunts",
        json={
            "pokemon": "pikachu",
            "displayName": "Pikachu",
            "spriteUrl": "https://example.com/pikachu.png",
            "game": None,
        },
    )
    return r.get_json()
