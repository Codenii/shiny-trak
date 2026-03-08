import os
import json
import threading
import time
import sys
from queue import Queue


if getattr(sys, "frozen", False):
    _BASE_DIR = os.path.dirname(sys.executable)

    import certifi

    os.environ["SSL_CERT_FILE"] = certifi.where()
    os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()
else:
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(_BASE_DIR, "data")
DATA_FILE = os.path.join(DATA_DIR, "hunts.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
GAMES_CACHE_DIR = os.path.join(DATA_DIR, "game_cache")
OVERLAYS_FILE = os.path.join(DATA_DIR, "overlays.json")

GAME_POKEDEX_MAP: dict[str, list[str]] = {
    "Red / Blue": ["kanto"],
    "Yellow": ["kanto"],
    "Gold / Silver": ["original-johto"],
    "Crystal": ["original-johto"],
    "Ruby / Sapphire": ["hoenn"],
    "FireRed / LeafGreen": ["kanto"],
    "Emerald": ["hoenn"],
    "Diamond / Pearl": ["original-sinnoh"],
    "Platinum": ["extended-sinnoh"],
    "HeartGold / SoulSilver": ["updated-johto"],
    "Black / White": ["original-unova"],
    "Black 2 / White 2": ["updated-unova"],
    "X / Y": ["kalos-central", "kalos-coastal", "kalos-mountain"],
    "Omega Ruby / Alpha Sapphire": ["updated-hoenn"],
    "Sun / Moon": ["original-alola"],
    "Ultra Sun / Ultra Moon": ["updated-alola"],
    "Let's Go Pikachu / Eevee": ["letsgo-kanto"],
    "Sword / Shield": ["galar", "isle-of-armor", "crown-tundra"],
    "Brilliant Diamond / Shining Pearl": ["updated-sinnoh"],
    "Legends: Arceus": ["hisui"],
    "Scarlet / Violet": ["paldea", "kitakami", "blueberry"],
    "Legends: Z-A": ["kalos-central", "kalos-coastal", "kalos-mountain"],
}

_game_pokemon_cache: dict[str, list[str]] = {}
_pokemon_list_cache = None

# SSE Client Registry
sse_clients: list[Queue] = []
sse_lock = threading.Lock()


def load_hunts() -> list:
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def save_hunts(hunts: list) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(hunts, f, indent=2)


def load_settings() -> dict:
    defaults = {
        "close_behavior": "ask",
        "mark_found_behavior": "ask",
    }
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(SETTINGS_FILE):
        return defaults
    try:
        with open(SETTINGS_FILE) as f:
            saved = json.load(f)
        return {**defaults, **saved}
    except (json.JSONDecodeError, OSError):
        return defaults


def save_settings(settings: dict) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)


def load_overlays() -> list:
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(OVERLAYS_FILE):
        return []
    try:
        with open(OVERLAYS_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def save_overlays(overlays: list) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(OVERLAYS_FILE, "w") as f:
        json.dump(overlays, f, indent=2)


def broadcast(hunts: list, overlays: list | None = None) -> None:
    if overlays is None:
        overlays = load_overlays()
    payload = json.dumps({"hunts": hunts, "overlays": overlays})
    with sse_lock:
        for q in list(sse_clients):
            try:
                q.put_nowait(payload)
            except Exception:
                pass
