import csv
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid
from queue import Empty, Queue

from flask import (
    Flask,
    Response,
    jsonify,
    render_template,
    request,
    redirect,
    stream_with_context,
)

import store
import tray
from hotkeys import PYNPUT_AVAILABLE, rebuild_hotkeys
from store import (
    GAME_POKEDEX_MAP,
    GAMES_CACHE_DIR,
    load_hunts,
    load_overlays,
    load_settings,
    save_hunts,
    save_overlays,
    save_settings,
    broadcast,
    sse_clients,
    sse_lock,
)
from tray import WEBVIEW_AVAILABLE, _on_closing, _setup_tray, _wait_for_server


if getattr(sys, "frozen", False):
    _TEMPLATE_DIR = os.path.join(sys._MEIPASS, "templates")
    _STATIC_DIR = os.path.join(sys._MEIPASS, "static")
else:
    _TEMPLATE_DIR = os.path.join(store._BASE_DIR, "templates")
    _STATIC_DIR = os.path.join(store._BASE_DIR, "static")

app = Flask(__name__, template_folder=_TEMPLATE_DIR, static_folder=_STATIC_DIR)

_http_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))


# Routes - Pages
@app.route("/")
def control_panel():
    return render_template("control.html")


@app.route('/overlay')
def overlay_default():
    return redirect('/overlay/main')


@app.route('/overlay/<name>')
def overlay(name):
    overlays = load_overlays()
    ov = next((o for o in overlays if o['name'].lower() == name.lower()), None)
    if ov is None:
        return 'Overlay not found', 404
    return render_template('overlay.html', overlay_id=ov['id'])


# Routes - SSE
@app.route("/events")
def events():
    def stream():
        q: Queue = Queue()
        with sse_lock:
            sse_clients.append(q)
        try:
            # Send current state on connect
            initial = json.dumps({"hunts": load_hunts(), 'overlays': load_overlays()})
            yield f"data: {initial}\n\n"
            while True:
                try:
                    payload = q.get(timeout=15)
                    yield f"data: {payload}\n\n"
                except Empty:
                    yield ": keepalive\n\n"
        except GeneratorExit:
            pass
        finally:
            with sse_lock:
                if q in sse_clients:
                    sse_clients.remove(q)

    return Response(
        stream_with_context(stream()),
        content_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# Routes - API
@app.get("/api/hunts")
def get_hunts():
    return jsonify(load_hunts())


@app.post("/api/hunts")
def add_hunt():
    data = request.json or {}

    hunt = {
        "id": str(uuid.uuid4()),
        "pokemon": data.get("pokemon", ""),
        "displayName": data.get("displayName", "Unknown"),
        "spriteUrl": data.get("spriteUrl") or None,
        "count": 0,
        "encounterRate": data.get("encounterRate") or None,
        "hotkey": data.get("hotkey") or None,
        "hotkeyDecrement": data.get("hotkeyDecrement") or None,
        "game": data.get("game") or None,
        "notes": "",
        "status": "active",
        "startDate": time.time(),
        "endDate": None,
        "createdAt": time.time(),
    }
    hunts = load_hunts()
    hunts.append(hunt)
    save_hunts(hunts)

    overlays = load_overlays()
    for o in overlays:
        if not any(h['huntId'] == hunt['id'] for h in o['hunts']):
            o['hunts'].append({'huntId': hunt['id'], 'visible': True})
            
    save_overlays(overlays)
    broadcast(hunts, overlays)
    rebuild_hotkeys()
    return jsonify(hunt), 201


@app.put("/api/hunts/<hunt_id>")
def update_hunt(hunt_id):
    hunts = load_hunts()
    hunt = next((h for h in hunts if h["id"] == hunt_id), None)
    if hunt is None:
        return jsonify({"error": "not found"}), 404

    data = request.json or {}
    allowed = {
        "displayName",
        "encounterRate",
        "hotkey",
        "hotkeyDecrement",
        "spriteUrl",
        "count",
        "game",
        "notes",
    }
    for k in allowed:
        if k in data:
            if k == "count":
                hunt["count"] = max(0, int(data[k]))
            elif k in ("hotkey", "hotkeyDecrement"):
                hunt[k] = data[k] or None
            else:
                hunt[k] = data[k]
    save_hunts(hunts)
    broadcast(hunts, load_overlays())
    rebuild_hotkeys()
    return jsonify(hunt)


@app.delete("/api/hunts/<hunt_id>")
def delete_hunt(hunt_id):
    overlays = load_overlays()
    for o in overlays:
        o['hunts'] = [h for h in o['hunts'] if h['huntId'] != hunt_id]

    hunts = load_hunts()
    hunts = [h for h in hunts if h["id"] != hunt_id]
    save_hunts(hunts)
    save_overlays(overlays)
    broadcast(hunts, overlays)
    rebuild_hotkeys()
    return jsonify({"ok": True})


@app.post("/api/hunts/<hunt_id>/increment")
def increment(hunt_id):
    hunts = load_hunts()
    hunt = next((h for h in hunts if h["id"] == hunt_id), None)
    if hunt is None:
        return jsonify({"error": "not found"}), 404
    hunt["count"] += 1
    save_hunts(hunts)
    broadcast(hunts, load_overlays())
    return jsonify(hunt)


@app.post("/api/hunts/<hunt_id>/decrement")
def decrement(hunt_id):
    hunts = load_hunts()
    hunt = next((h for h in hunts if h["id"] == hunt_id), None)
    if hunt is None:
        return jsonify({"error": "not found"}), 404
    hunt["count"] = max(0, hunt["count"] - 1)
    save_hunts(hunts)
    broadcast(hunts, load_overlays())
    return jsonify(hunt)


@app.post("/api/hunts/<hunt_id>/reset")
def reset(hunt_id):
    hunts = load_hunts()
    hunt = next((h for h in hunts if h["id"] == hunt_id), None)
    if hunt is None:
        return jsonify({"error": "not found"}), 404
    hunt["count"] = 0
    save_hunts(hunts)
    broadcast(hunts, load_overlays())
    return jsonify(hunt)


@app.post("/api/hunts/<hunt_id>/complete")
def complete_hunt(hunt_id):
    hunts = load_hunts()
    hunt = next((h for h in hunts if h["id"] == hunt_id), None)
    if hunt is None:
        return jsonify({"error": "not found"}), 404
    data = request.get_json(silent=True) or {}
    hunt["status"] = "completed"
    hunt["endDate"] = time.time()
    if "notes" in data:
        hunt["notes"] = data["notes"]
    save_hunts(hunts)
    broadcast(hunts, load_overlays())
    rebuild_hotkeys()
    return jsonify(hunt)


@app.get("/api/pokemon/<name>")
def lookup_pokemon(name):
    url = f"https://pokeapi.co/api/v2/pokemon/{name.lower().strip()}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "shiny-trak/1.0"})
        with _http_opener.open(req, timeout=8) as resp:
            data = json.loads(resp.read())
        display = data["name"].replace("-", " ").title()
        return jsonify(
            {
                "id": data["id"],
                "pokemon": data["name"],
                "displayName": display,
                "spriteUrl": data["sprites"]["front_shiny"],
            }
        )
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return jsonify({"error": "Pokemon not found"}), 404
        return jsonify({"error": f"PokeAPI error {e.code}"}), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def pynput_to_hs(hotkey_str):
    MOD_MAP = {"<ctrl>": "ctrl", "<shift>": "shift", "<alt>": "alt", "<cmd>": "cmd"}
    KEY_MAP = {
        "<f1>": "f1",
        "<f2>": "f2",
        "<f3>": "f3",
        "<f4>": "f4",
        "<f5>": "f5",
        "<f6>": "f6",
        "<f7>": "f7",
        "<f8>": "f8",
        "<f9>": "f9",
        "<f10>": "f10",
        "<f11>": "f11",
        "<f12>": "f12",
        "<up>": "up",
        "<down>": "down",
        "<left>": "left",
        "<right>": "right",
        "<space>": "space",
        "<enter>": "return",
        "<esc>": "escape",
        "<tab>": "tab",
        "<backspace>": "delete",
        "<home>": "home",
        "<end>": "end",
        "<page_up>": "pageup",
        "<page_down>": "pagedown",
    }

    parts = hotkey_str.split("+")
    mods, key = [], None
    for p in parts:
        if p in MOD_MAP:
            mods.append(MOD_MAP[p])
        else:
            key = KEY_MAP.get(p, p.strip("<>").lower())
    return (mods, key) if key else None


@app.get("/api/hammerspoon")
def hammerspoon_config():
    hunts = load_hunts()
    lines = [
        "-- Auto-generated by Shiny Trak",
        "local function _post(url)",
        '  hs.http.asyncPost(url, "", {}, function() end)',
        "end",
        'local BASE = "http://localhost:3000"',
        "",
    ]
    for hunt in hunts:
        name = hunt.get("displayName", "unknown")
        hunt_id = hunt["id"]
        for field, action in [
            ("hotkey", "increment"),
            ("hotkeyDecrement", "decrement"),
        ]:
            if hunt.get(field):
                result = pynput_to_hs(hunt[field])
                if result:
                    mods, key = result
                    mods_lua = "{" + ", ".join(f'"{m}"' for m in mods) + "}"
                    lines.append(f"-- {name} {action}")
                    lines.append(
                        f'hs.hotkey.bind({mods_lua}, "{key}", function() _post(BASE .. "/api/hunts/{hunt_id}/{action}") end)'
                    )
    return "\n".join(lines), 200, {"Content-Type": "text/plain; charset=utf-8"}


@app.get("/api/pokemon-list")
def pokemon_list():
    global _pokemon_list_cache
    if store._pokemon_list_cache is not None:
        return jsonify(store._pokemon_list_cache)

    try:
        req = urllib.request.Request(
            "https://pokeapi.co/api/v2/pokemon?limit=10000",
            headers={"User-Agent": "shiny-trak/1.0"},
        )
        with _http_opener.open(req, timeout=10) as resp:
            data = json.loads(resp.read())
        _pokemon_list_cache = [p["name"] for p in data["results"]]
        return jsonify(_pokemon_list_cache)
    except Exception as e:
        return jsonify([])


@app.get("/api/pokemon-list/game/<path:game>")
def pokemon_list_by_game(game):
    if game not in GAME_POKEDEX_MAP:
        return jsonify({"error": "Unknown game"}), 404

    # In memory cache hit
    if game in store._game_pokemon_cache:
        return jsonify(store._game_pokemon_cache[game])

    # Disk cache hit (30 day expiry)
    os.makedirs(GAMES_CACHE_DIR, exist_ok=True)
    cache_file = os.path.join(
        GAMES_CACHE_DIR, f"{game.replace('/', '_').replace(' ', '_')}.json"
    )
    if os.path.exists(cache_file):
        try:
            with open(cache_file) as f:
                cached = json.load(f)
            if time.time() - cached.get("ts", 0) < 86400 * 30:
                store._game_pokemon_cache[game] = cached["names"]
                return jsonify(cached["names"])
        except (json.JSONDecodeError, OSError, KeyError):
            pass

    # Fetch from PokeAPI
    names = set()
    for pokedex_id in GAME_POKEDEX_MAP[game]:
        try:
            url = f"https://pokeapi.co/api/v2/pokedex/{pokedex_id}/"
            req = urllib.request.Request(url, headers={"User-Agent": "shiny-trak/1.0"})
            with _http_opener.open(req, timeout=10) as resp:
                data = json.loads(resp.read())
            for entry in data["pokemon_entries"]:
                names.add(entry["pokemon_species"]["name"])
        except Exception:
            pass

    if not names:
        return jsonify({"error": "Failed to fetch game data"}), 502

    result = sorted(names)

    # Write disk cache
    try:
        with open(cache_file, "w") as f:
            json.dump({"ts": time.time(), "names": result}, f)
    except OSError:
        pass

    store._game_pokemon_cache[game] = result
    return jsonify(result)


@app.post("/api/pokemon-list/game/<path:game>/refresh")
def refresh_game_cache(game):
    if game not in GAME_POKEDEX_MAP:
        return jsonify({"error": "Unknown game"}), 404

    # Clear caches and re-fetch data
    store._game_pokemon_cache.pop(game, None)
    cache_file = os.path.join(
        GAMES_CACHE_DIR, f"{game.replace('/', '_').replace(' ', '_')}.json"
    )
    try:
        os.remove(cache_file)
    except OSError:
        pass

    return pokemon_list_by_game(game)


@app.get("/api/export")
def export_hunts():
    scope = request.args.get("scope", "all")
    fmt = request.args.get("format", "json")

    hunts = load_hunts()
    if scope == "active":
        hunts = [h for h in hunts if h.get("status", "active") == "active"]
    elif scope == "completed":
        hunts = [h for h in hunts if h.get("status") == "completed"]

    filename = f"shiny-trak-{scope}.{fmt}"
    download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
    os.makedirs(download_dir, exist_ok=True)
    filepath = os.path.join(download_dir, filename)

    if fmt == "csv":
        fields = [
            "displayName",
            "pokemon",
            "game",
            "count",
            "status",
            "startDate",
            "endDate",
            "notes",
        ]
        with open(filepath, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            for h in hunts:
                row = dict(h)
                row["startDate"] = (
                    time.strftime("%Y-%m-%d", time.localtime(h["startDate"]))
                    if h.get("startDate")
                    else ""
                )
                row["endDate"] = (
                    time.strftime("%Y-%m-%d", time.localtime(h["endDate"]))
                    if h.get("endDate")
                    else ""
                )
                writer.writerow(row)
    else:
        with open(filepath, "w") as f:
            json.dump(hunts, f, indent=2)

    return jsonify({"ok": True, "filename": filename})


@app.post("/api/shutdown")
def shutdown():
    def _stop():
        time.sleep(0.5)
        os._exit(0)

    threading.Thread(target=_stop, daemon=True).start()
    return jsonify({"ok": True})


@app.get("/api/settings")
def get_settings():
    return jsonify(load_settings())


@app.put("/api/settings")
def update_settings():
    data = request.json or {}
    settings = load_settings()
    for k in {"close_behavior", "mark_found_behavior"}:
        if k in data:
            settings[k] = data[k]
    save_settings(settings)
    return jsonify(settings)


@app.get("/api/games")
def get_games():
    return jsonify(list(GAME_POKEDEX_MAP.keys()))


@app.post("/api/close-action")
def close_action():
    action = (request.json or {}).get("action", "cancel")
    if action == "quit":

        def _quit():
            time.sleep(0.05)
            tray._quitting = True
            if tray._webview_window:
                tray._webview_window.destroy()

        threading.Thread(target=_quit, daemon=True).start()
    elif action == "minimize":
        if tray._webview_window:
            tray._webview_window.hide()
    return jsonify({"ok": True})


def migrate_overlays() -> None:
    overlays = load_overlays()
    hunts = load_hunts()
    changed = False
    for o in overlays:
        elements = o.setdefault('elements', {})
        if 'odds' not in elements:
            elements['odds'] = False
            changed = True
    for h in hunts:
        if "displayMode" in h:
            del h["displayMode"]
            changed = True
    if changed:
        save_hunts(hunts)
        save_overlays(overlays)
    if overlays:
        return
    overlay = {
        "id": str(uuid.uuid4()),
        "name": "main",
        "elements": {
            "sprite": True,
            "name": True,
            "count": True,
            "odds": False,
        },
        "hunts": [{"huntId": h["id"], "visible": True} for h in hunts],
    }
    save_overlays([overlay])


@app.get('/api/overlays')
def get_overlays():
    return jsonify(load_overlays())


@app.post('/api/overlays')
def add_overlay():
    data = request.json or {}
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'error': 'name required'}), 400
    hunts = load_hunts()
    overlay = {
        'id': str(uuid.uuid4()),
        'name': name,
        'elements': {'sprite': True, 'name': True, 'count': True, 'odds': False},
        'hunts': [{'huntId': h['id'], 'visible': True} for h in hunts if h.get('status', 'active') == 'active'],
    }
    overlays = load_overlays()
    overlays.append(overlay)
    save_overlays(overlays)
    broadcast(hunts, overlays)
    return jsonify(overlay), 201


@app.put('/api/overlays/<overlay_id>')
def update_overlay(overlay_id):
    overlays = load_overlays()
    overlay = next((o for o in overlays if o['id'] == overlay_id), None)
    if overlay is None:
        return jsonify({'error': 'not found'}), 404
    data = request.json or {}
    if 'name' in data:
        overlay['name'] = data['name'].strip()
    if 'hunts' in data:
        overlay['hunts'] = data['hunts']
    if 'elements' in data:
        overlay['elements'] = data['elements']
    save_overlays(overlays)
    broadcast(load_hunts(), overlays)
    return jsonify(overlay)


@app.delete('/api/overlays/<overlay_id>')
def delete_overlay(overlay_id):
    overlays = load_overlays()
    if len(overlays) <= 1:
        return jsonify({'error': 'cannot delete the last overlay'}), 400
    overlays = [o for o in overlays if o['id'] != overlay_id]
    save_overlays(overlays)
    broadcast(load_hunts(), overlays)
    return jsonify({'ok': True})


# Start
if __name__ == "__main__":
    rebuild_hotkeys()
    migrate_overlays()

    threading.Thread(
        target=lambda: app.run(
            host="127.0.0.1", port=3000, threaded=True, use_reloader=False
        ),
        daemon=True,
    ).start()
    _wait_for_server()

    if WEBVIEW_AVAILABLE:
        import webview

        tray._webview_window = webview.create_window(
            "Shiny Trak",
            "http://127.0.0.1:3000",
            width=1100,
            height=700,
            min_size=(820, 560),
            text_select=False,
            background_color="#0D0B1A",
        )
        tray._webview_window.events.closing += _on_closing
        webview.start(func=_setup_tray, args=(tray._webview_window,))
        os._exit(0)
    else:
        print("Shiny Trak running at    http://127.0.0.1:3000")
        print("OBS overlay URL          http://127.0.0.1:3000/overlay")
        if not PYNPUT_AVAILABLE:
            print("WARNING: pynput not installed - hotkeys unavailable")
        app.run(host="127.0.0.1", port=3000, threaded=True, use_reloader=False)
