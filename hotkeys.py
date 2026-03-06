import platform
import threading

from store import broadcast, load_hunts, save_hunts


try:
    if platform.system() == "Darwin":
        raise ImportError
    from pynput import keyboard as pynput_keyboard

    PYNPUT_AVAILABLE = True
except Exception:
    PYNPUT_AVAILABLE = False
    print("[hotkeys] pynput is not available - hotkeys disabled")

hotkey_listener = None
hotkey_lock = threading.Lock()


def increment_hunt_by_id(hunt_id: str) -> None:
    print(f"[hotkeys] Increment fired for {hunt_id}")
    hunts = load_hunts()
    for h in hunts:
        if h["id"] == hunt_id:
            h["count"] += 1
            save_hunts(hunts)
            broadcast(hunts)
            return


def decrement_hunt_by_id(hunt_id: str) -> None:
    print(f"[hotkeys] Decrement fired for {hunt_id}")
    hunts = load_hunts()
    for h in hunts:
        if h["id"] == hunt_id:
            h["count"] = max(0, h["count"] - 1)
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
        active_hunts = [h for h in hunts if h.get("status", "active") == "active"]
        hotkey_map = {}
        for h in active_hunts:
            if h.get("hotkey"):
                hotkey_map[h["hotkey"]] = lambda hid=h["id"]: increment_hunt_by_id(hid)
            if h.get("hotkeyDecrement"):
                hotkey_map[h["hotkeyDecrement"]] = lambda hid=h[
                    "id"
                ]: decrement_hunt_by_id(hid)
        print(f"[hotkey] Registering: {list(hotkey_map.keys())}")
        if not hotkey_map:
            return
        try:
            listener = pynput_keyboard.GlobalHotKeys(hotkey_map)
            listener.daemon = True
            listener.start()
            hotkey_listener = listener
        except Exception as e:
            print(f"[hotkeys] Failed to start listener: {e}")
