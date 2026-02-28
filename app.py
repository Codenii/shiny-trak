import json
import os
import threading
import time
import urllib.request
import urllib.error
import uuid
from queue import Queue, Empty
from flask import Flask, Response, jsonify, render_template, request, stream_with_context

try:
    from pynput import keyboard as pynput_keyboard
    PYNPUT_AVAILABLE = True
except:
    PYNPUT_AVAILABLE = False
    print("[hotkeys] pynput not available - hotkeys disabled")


app = Flask(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DATA_FILE = os.path.join(DATA_DIR, "hunts.json")

_pokemon_list_cache = None


# SSE Client Registry
sse_clients: list[Queue] = []
sse_lock = threading.Lock()

# Global hotkey listener
hotkey_listener = None
hotkey_lock = threading.Lock()

# Data Helpers
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


# SSE Broadcast
def broadcast(hunts: list) -> None:
    payload = json.dumps({"hunts": hunts})
    with sse_lock:
        for q in list(sse_clients):
            try:
                q.put_nowait(payload)
            except Exception:
                pass


# Hotkeys
def increment_hunt_by_id(hunt_id: str) -> None:
    print(f'[hotkeys] Increment fired for {hunt_id}')
    hunts = load_hunts()
    for h in hunts:
        if h["id"] == hunt_id:
            h['count'] += 1
            save_hunts(hunts)
            broadcast(hunts)
            return


def decrement_hunt_by_id(hunt_id: str) -> None:
    print(f'[hotkeys] Decrement fired for {hunt_id}')
    hunts = load_hunts()
    for h in hunts:
        if h['id'] == hunt_id:
            h['count'] = max(0, h['count'] - 1)
            save_hunts(hunts)
            broadcast(hunts)
            return


def rebuild_hotkeys() -> None:
    global hotkey_listener
    if not PYNPUT_AVAILABLE:
        return
    with hotkey_lock:
        if hotkey_listener is not None:
            try:
                hotkey_listener.stop()
            except Exception:
                pass
            hotkey_listener = None

        hunts = load_hunts()
        hotkey_map = {}
        for h in hunts:
            if h.get('hotkey'):
                hotkey_map[h['hotkey']] = (lambda hid=h['id']: increment_hunt_by_id(hid))
            if h.get('hotkeyDecrement'):
                hotkey_map[h['hotkeyDecrement']] = (lambda hid=h['id']: decrement_hunt_by_id(hid))
        print(f'[hotkey] Registering: {list(hotkey_map.keys())}')
        if not hotkey_map:
            return
        try:
            listener = pynput_keyboard.GlobalHotKeys(hotkey_map)
            listener.daemon = True
            listener.start()
            hotkey_listener = listener
        except Exception as e:
            print(f"[hotkeys] Failed to start listener: {e}")


# Routes - Pages
@app.route('/')
def control_panel():
    return render_template('control.html')


@app.route('/overlay')
def overlay():
    return render_template('overlay.html')


# Routes - SSE
@app.route('/events')
def events():
    def stream():
        q: Queue = Queue()
        with sse_lock:
            sse_clients.append(q)
        try:
            # Send current state on connect
            initial = json.dumps({'hunts': load_hunts()})
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
@app.get('/api/hunts')
def get_hunts():
    return jsonify(load_hunts())


@app.post('/api/hunts')
def add_hunt():
    data = request.json or {}
    hunt = {
        'id': str(uuid.uuid4()),
        'pokemon': data.get('pokemon', ''),
        'displayName': data.get('displayName', 'Unknown'),
        'spriteUrl': data.get('spriteUrl') or None,
        'count': 0,
        'displayMode': data.get('displayMode', 'full'),
        'hotkey': data.get('hotkey') or None,
        'hotkeyDecrement': data.get('hotkeyDecrement') or None,
        'createdAt': time.time(),
    }
    hunts = load_hunts()
    hunts.append(hunt)
    save_hunts(hunts)
    broadcast(hunts)
    rebuild_hotkeys()
    return jsonify(hunt), 201


@app.put('/api/hunts/<hunt_id>')
def update_hunt(hunt_id):
    hunts = load_hunts()
    hunt = next((h for h in hunts if h['id'] == hunt_id), None)
    if hunt is None:
        return jsonify({"error": "not found"}), 404
    
    data = request.json or {}
    allowed = {"displayName", "displayMode", "hotkey", "hotkeyDecrement", "spriteUrl", "count"}
    for k in allowed:
        if k in data:
            if k == 'count':
                hunt['count'] = max(0, int(data[k]))
            elif k in ('hotkey', 'hotkeyDecrement'):
                hunt[k] = data[k] or None
            else:
                hunt[k] = data[k]
    save_hunts(hunts)
    broadcast(hunts)
    rebuild_hotkeys()
    return jsonify(hunt)


@app.delete('/api/hunts/<hunt_id>')
def delete_hunt(hunt_id):
    hunts = load_hunts()
    hunts = [h for h in hunts if h['id'] != hunt_id]
    save_hunts(hunts)
    broadcast(hunts)
    rebuild_hotkeys()
    return jsonify({'ok': True})


@app.post('/api/hunts/<hunt_id>/increment')
def increment(hunt_id):
    hunts = load_hunts()
    hunt = next((h for h in hunts if h['id'] == hunt_id), None)
    if hunt is None:
        return jsonify({'error': 'not found'}), 404
    hunt['count'] += 1
    save_hunts(hunts)
    broadcast(hunts)
    return jsonify(hunt)


@app.post('/api/hunts/<hunt_id>/decrement')
def decrement(hunt_id):
    hunts = load_hunts()
    hunt = next((h for h in hunts if h['id'] == hunt_id), None)
    if hunt is None:
        return jsonify({'error': 'not found'}), 404
    hunt['count'] = max(0, hunt['count'] - 1)
    save_hunts(hunts)
    broadcast(hunts)
    return jsonify(hunt)


@app.post('/api/hunts/<hunt_id>/reset')
def reset(hunt_id):
    hunts = load_hunts()
    hunt = next((h for h in hunts if h['id'] == hunt_id), None)
    if hunt is None:
        return jsonify({'error': 'not found'}), 404
    hunt['count'] = 0
    save_hunts(hunts)
    broadcast(hunts)
    return jsonify(hunt)


@app.get('/api/pokemon/<name>')
def lookup_pokemon(name):
    url = f"https://pokeapi.co/api/v2/pokemon/{name.lower().strip()}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'shiny-trak/1.0'})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read())
        display = data['name'].replace('-', ' ').title()
        return jsonify({
            'id': data['id'],
            'pokemon': data['name'],
            'displayName': display,
            'spriteUrl': data['sprites']['front_shiny'],
        })
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return jsonify({'error': 'Pokemon not found'}), 404
        return jsonify({'error': f"PokeAPI error {e.code}"}), 502
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def pynput_to_hs(hotkey_str):
    MOD_MAP = {'<ctrl>': 'ctrl', '<shift>': 'shift', '<alt>': 'alt', '<cmd>': 'cmd'}
    KEY_MAP = {
        '<f1>': 'f1', '<f2>': 'f2', '<f3>': 'f3', '<f4>': 'f4',
        '<f5>': 'f5', '<f6>': 'f6', '<f7>': 'f7', '<f8>': 'f8',
        '<f9>': 'f9', '<f10>': 'f10', '<f11>': 'f11', '<f12>': 'f12',
        '<up>': 'up', '<down>': 'down', '<left>': 'left', '<right>': 'right',
        '<space>': 'space', '<enter>': 'return', '<esc>': 'escape',
        '<tab>': 'tab', '<backspace>': 'delete', '<home>': 'home',
        '<end>': 'end', '<page_up>': 'pageup', '<page_down>': 'pagedown',
    }

    parts = hotkey_str.split('+')
    mods, key = [], None
    for p in parts:
        if p in MOD_MAP:
            mods.append(MOD_MAP[p])
        else:
            key = KEY_MAP.get(p, p.strip('<>').lower())
    return (mods, key) if key else None


@app.get('/api/hammerspoon')
def hammerspoon_config():
    hunts = load_hunts()
    lines = [
        '-- Auto-generated by Shiny Trak',
        'local function _post(url)',
        '  hs.http.asyncPost(url, "", {}, function() end)',
        'end',
        'local BASE = "http://localhost:3000"',
        '',
    ]
    for hunt in hunts:
        name = hunt.get('displayName', 'unknown')
        hunt_id = hunt['id']
        for field, action in [('hotkey', 'increment'), ('hotkeyDecrement', 'decrement')]:
            if hunt.get(field):
                result = pynput_to_hs(hunt[field])
                if result:
                    mods, key = result
                    mods_lua = '{' + ', '.join(f'"{m}"' for m in mods) + '}'
                    lines.append(f'-- {name} {action}')
                    lines.append(f'hs.hotkey.bind({mods_lua}, "{key}", function() _post(BASE .. "/api/hunts/{hunt_id}/{action}") end)')
    return '\n'.join(lines), 200, {'Content-Type': 'text/plain; charset=utf-8'}


@app.get('/api/pokemon-list')
def pokemon_list():
    global _pokemon_list_cache
    if _pokemon_list_cache is not None:
        return jsonify(_pokemon_list_cache)
    
    try:
        req = urllib.request.Request(
            'https://pokeapi.co/api/v2/pokemon?limit=10000',
            headers={'User-Agent': 'shiny-trak/1.0'}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        _pokemon_list_cache = [p['name'] for p in data['results']]
        return jsonify(_pokemon_list_cache)
    except Exception as e:
        return jsonify([])


# Start
if __name__ == "__main__":
    rebuild_hotkeys()
    print("Shiny Trak running at    http://localhost:3000")
    print("OBS overlay URL:         http://localhost:3000/overlay")
    print("Control Panel:           http://localhost:3000/")
    if not PYNPUT_AVAILABLE:
        print("WARNING: pynput not installed - hotkeys unavailable")
    app.run(host="0.0.0.0", port=3000, threaded=True)