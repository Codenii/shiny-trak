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
    redirect,
    render_template,
    request,
    stream_with_context,
)
from waitress import serve

import store
import tray
from hotkeys import PYNPUT_AVAILABLE, rebuild_hotkeys
from store import (
    GAME_POKEDEX_MAP,
    GAMES_CACHE_DIR,
    broadcast,
    broadcast_milestone,
    load_hunts,
    load_overlays,
    load_settings,
    save_hunts,
    save_overlays,
    save_settings,
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


@app.route("/overlay")
def overlay_default():
    return "", 404


@app.route("/overlay/<name>")
def overlay(name):
    overlays = load_overlays()
    if name.endswith("-hunt"):
        base = name[:-5]
        ov = next(
            (
                o
                for o in overlays
                if o["name"].lower() == base.lower()
                and (o.get("type", "hunt") == "hunt")
            ),
            None,
        )
    elif name.endswith("-stats"):
        base = name[:-6]
        ov = next(
            (
                o
                for o in overlays
                if o["name"].lower() == base.lower() and o.get("type") == "stats"
            ),
            None,
        )
    else:
        ov = next((o for o in overlays if o["name"].lower() == name.lower()), None)

    if ov is None:
        return "Overlay not found", 404
    return render_template("overlay.html", overlay_id=ov["id"])


# Routes - SSE
@app.route("/events")
def events():
    def stream():
        q: Queue = Queue()
        with sse_lock:
            sse_clients.append(q)
        try:
            # Send current state on connect
            initial = json.dumps({"hunts": load_hunts(), "overlays": load_overlays()})
            yield f"data: {initial}\n\n"
            while True:
                try:
                    payload = q.get(timeout=15)
                    yield payload
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
    hunts = load_hunts()
    scope = request.args.get("scope", "active")
    if scope == "active":
        hunts = [h for h in hunts if h.get("status", "active") == "active"]
    elif scope == "completed":
        hunts = [h for h in hunts if h.get("status") == "completed"]
    return jsonify(hunts)


@app.post("/api/hunts")
def add_hunt():
    data = request.json or {}

    pokemon = data.get("pokemon", "").strip()
    if not pokemon:
        return jsonify({"error": "pokemon required"}), 400

    display_name = data.get("displayName", "").strip()
    if not display_name:
        return jsonify({"error": "displayName required"}), 400

    hunt = {
        "id": str(uuid.uuid4()),
        "pokemon": pokemon,
        "displayName": display_name,
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

    broadcast(hunts, load_overlays())
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
        "startDate",
        "endDate",
    }
    for k in allowed:
        if k in data:
            if k == "count":
                try:
                    hunt["count"] = max(0, int(data[k]))
                except (ValueError, TypeError):
                    return jsonify({"error": "count must be a number"}), 400
            elif k == "encounterRate":
                if data[k] is not None:
                    try:
                        val = int(data[k])
                    except (ValueError, TypeError):
                        return (
                            jsonify(
                                {
                                    "error": "encounterRate must be a positive integer or null"
                                }
                            ),
                            400,
                        )
                    if val <= 0:
                        return (
                            jsonify(
                                {
                                    "error": "encounterRate must be a positive integer or null"
                                }
                            ),
                            400,
                        )
                    hunt[k] = val
                else:
                    hunt[k] = None
            elif k == "displayName":
                if not isinstance(data[k], str) or not data[k].strip():
                    return (
                        jsonify({"error": "displayName must be a non-empty string"}),
                        400,
                    )
                hunt[k] = data[k]
            elif k in ("game", "notes", "spriteUrl"):
                if data[k] is not None and not isinstance(data[k], str):
                    return jsonify({"error": f"{k} must be a string or null"}), 400
                hunt[k] = data[k]
            elif k in ("hotkey", "hotkeyDecrement"):
                hunt[k] = data[k] or None
            elif k in ("startDate", "endDate"):
                if data[k] is not None:
                    try:
                        hunt[k] = float(data[k])
                    except (ValueError, TypeError):
                        return jsonify({"error": f"{k} must be a number or null"}), 400
                else:
                    hunt[k] = None

    save_hunts(hunts)
    broadcast(hunts, load_overlays())
    rebuild_hotkeys()
    return jsonify(hunt)


@app.delete("/api/hunts/<hunt_id>")
def delete_hunt(hunt_id):
    overlays = load_overlays()
    for o in overlays:
        if o.get("type", "hunt") != "hunt":
            continue
        o["hunts"] = [h for h in o["hunts"] if h["huntId"] != hunt_id]

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
    rate = hunt.get("encounterRate")
    if rate and hunt["count"] % rate == 0:
        settings = load_settings()
        if settings.get("milestone_alerts", True):
            broadcast_milestone(hunt)
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
    os.makedirs(store.DOWNLOAD_DIR, exist_ok=True)
    filepath = os.path.join(store.DOWNLOAD_DIR, filename)

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

    if "close_behavior" in data:
        if data["close_behavior"] not in ("ask", "minimize", "quit"):
            return (
                jsonify(
                    {"error": "close_behavior must be 'ask', 'minimize', or 'quit'"}
                ),
                400,
            )
        settings["close_behavior"] = data["close_behavior"]

    if "mark_found_behavior" in data:
        if data["mark_found_behavior"] not in ("ask", "never"):
            return (
                jsonify({"error": "mark_found_behavior must be 'ask' or 'never'"}),
                400,
            )
        settings["mark_found_behavior"] = data["mark_found_behavior"]

    if "milestone_alerts" in data:
        if not isinstance(data["milestone_alerts"], bool):
            return jsonify({"error": "milestone_alerts must be a boolean"}), 400
        settings["milestone_alerts"] = data["milestone_alerts"]
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
        elements = o.setdefault("elements", {})
        if "odds" not in elements:
            elements["odds"] = False
            changed = True
        if "type" not in o:
            o["type"] = "hunt"
            changed = True
    for h in hunts:
        if "displayMode" in h:
            del h["displayMode"]
            changed = True
    if changed:
        save_hunts(hunts)
        save_overlays(overlays)


@app.get("/api/overlays")
def get_overlays():
    return jsonify(load_overlays())


@app.post("/api/overlays")
def add_overlay():
    data = request.json or {}
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "name required"}), 400
    overlay_type = data.get("type", "hunt")
    if overlay_type not in ("hunt", "stats"):
        return jsonify({"error": "type must be hunt or stats"}), 400

    hunts = load_hunts()

    if overlay_type == "hunt":
        overlay = {
            "id": str(uuid.uuid4()),
            "name": name,
            "type": "hunt",
            "elements": {"sprite": True, "name": True, "count": True, "odds": False},
            "hunts": [],
        }
    else:
        overlay = {
            "id": str(uuid.uuid4()),
            "name": name,
            "type": "stats",
            "elements": {
                "totalCompleted": True,
                "breakdown": "completed",
            },
            "game": None,
        }

    overlays = load_overlays()
    overlays.append(overlay)
    save_overlays(overlays)
    broadcast(hunts, overlays)
    return jsonify(overlay), 201


@app.put("/api/overlays/<overlay_id>")
def update_overlay(overlay_id):
    overlays = load_overlays()
    overlay = next((o for o in overlays if o["id"] == overlay_id), None)
    if overlay is None:
        return jsonify({"error": "not found"}), 404
    data = request.json or {}

    if "name" in data:
        name = data["name"].strip()
        if not name:
            return jsonify({"error": "name is required"}), 400
        overlay["name"] = name

    if "hunts" in data:
        hunt_data = data["hunts"]
        if not isinstance(hunt_data, list):
            return jsonify({"error": "hunts must be a list"}), 400
        for entry in hunt_data:
            if not isinstance(entry.get("huntId"), str) or not isinstance(
                entry.get("visible"), bool
            ):
                return (
                    jsonify(
                        {
                            "error": "each hunt entry must have huntId (string) and visible (boolean)"
                        }
                    ),
                    400,
                )
        overlay["hunts"] = hunt_data

    if "elements" in data:
        elements = data["elements"]
        if not isinstance(elements, dict):
            return jsonify({"error": "elements must be an object"}), 400
        ov_type = overlay.get("type", "hunt")
        if ov_type == "hunt":
            hunt_keys = {"sprite", "name", "count", "odds"}
            if set(elements.keys()) != hunt_keys:
                return (
                    jsonify(
                        {
                            "error": f"hunt overlay elements must contain exactly: {sorted(hunt_keys)}"
                        }
                    ),
                    400,
                )
            if not all(isinstance(elements[k], bool) for k in hunt_keys):
                return (
                    jsonify({"error": "hunt overlay elements must all be booleans"}),
                    400,
                )
        elif ov_type == "stats":
            if not isinstance(elements.get("totalCompleted"), bool):
                return jsonify({"error": "totalCompleted must be a boolean"}), 400
            if elements.get("breakdown") not in ("completed", "active", None):
                return (
                    jsonify(
                        {"error": "breakdown must be 'completed', 'active', or null"}
                    ),
                    400,
                )
        overlay["elements"] = elements

    if "game" in data:
        if data["game"] is not None and not isinstance(data["game"], str):
            return jsonify({"error": "game must be a string or null"}), 400
        overlay["game"] = data["game"]

    save_overlays(overlays)
    broadcast(load_hunts(), overlays)
    return jsonify(overlay)


@app.delete("/api/overlays/<overlay_id>")
def delete_overlay(overlay_id):
    overlays = load_overlays()
    overlays = [o for o in overlays if o["id"] != overlay_id]
    save_overlays(overlays)
    broadcast(load_hunts(), overlays)
    return "", 204


# Stats
@app.get("/api/stats")
def get_stats():
    hunts = load_hunts()
    by_game = {}
    for hunt in hunts:
        game = hunt.get("game") or None
        if game not in by_game:
            by_game[game] = {"completed": 0, "active": 0}
        status = hunt.get("status", "active")
        if status == "completed":
            by_game[game]["completed"] += 1
        else:
            by_game[game]["active"] += 1

    return jsonify(
        {
            "totalCompleted": sum(1 for h in hunts if h.get("status") == "completed"),
            "totalActive": sum(
                1 for h in hunts if h.get("status", "active") == "active"
            ),
            "byGame": {str(k): v for k, v in by_game.items()},
        }
    )


# Start
if __name__ == "__main__":
    rebuild_hotkeys()
    migrate_overlays()

    threading.Thread(
        target=lambda: serve(app, host="127.0.0.1", port=3000, threads=8),
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
        os.environ["WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS"] = "--no-proxy-server"
        webview.start(func=_setup_tray, args=(tray._webview_window,))
        os._exit(0)
    else:
        print("Shiny Trak running at    http://127.0.0.1:3000")
        print("OBS overlay URL          http://127.0.0.1:3000/overlay")
        if not PYNPUT_AVAILABLE:
            print("WARNING: pynput not installed - hotkeys unavailable")
        serve(app, host="127.0.0.1", port=3000, threads=8)
