import os
import socket
import tempfile
import threading
import time

import pytest

import store
from app import app, migrate_overlays


def _find_free_port() -> int:
    with socket.socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def live_server():
    tmp: str = tempfile.mkdtemp()
    store.DATA_DIR = tmp
    store.DATA_FILE = os.path.join(tmp, "hunts.json")
    store.OVERLAYS_FILE = os.path.join(tmp, "overlays.json")
    store.SETTINGS_FILE = os.path.join(tmp, "settings.json")
    store.DOWNLOAD_DIR = tmp
    store._pokemon_list_cache = None
    store._game_pokemon_cache.clear()

    migrate_overlays()

    port = _find_free_port()
    threading.Thread(
        target=lambda: app.run(
            host="127.0.0.1", port=port, use_reloader=False, threaded=True
        ),
        daemon=True,
    ).start()

    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                break
        except OSError:
            time.sleep(0.05)

    yield f"http://127.0.0.1:{port}"


@pytest.fixture(scope="session")
def base_url(live_server):
    return live_server


@pytest.fixture(autouse=True)
def isolate_data():
    pass
