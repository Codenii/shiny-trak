import ctypes
import platform
import threading

from store import broadcast, load_hunts, load_overlays, save_hunts


# pynput (Windows / Linux)
PYNPUT_AVAILABLE = False
if platform.system() != "Darwin":
    try:
        from pynput import keyboard as pynput_keyboard

        PYNPUT_AVAILABLE = True
    except Exception:
        print("[hotkeys] pynput is not available - hotkeys disabled")


# NSEvent (macOS)
MACOS_AVAILABLE = False
if platform.system() == "Darwin":
    try:
        from AppKit import NSEvent

        MACOS_AVAILABLE = True
    except ImportError:
        print("[hotkeys] AppKit not available - hotkeys disabled on macOS")


_NS_SHIFT = 1 << 17
_NS_CTRL = 1 << 18
_NS_ALT = 1 << 19
_NS_CMD = 1 << 20
_NS_MOD_MASK = _NS_SHIFT | _NS_CTRL | _NS_ALT | _NS_CMD
_NS_KEY_DOWN = 1 << 10

_PYNPUT_MOD_TO_NS = {
    "<shift>": _NS_SHIFT,
    "<ctrl>": _NS_CTRL,
    "<alt>": _NS_ALT,
    "<cmd>": _NS_CMD,
}

_PYNPUT_KEY_TO_CODE = {
    "<f1>": 122,
    "<f2>": 120,
    "<f3>": 99,
    "<f4>": 118,
    "<f5>": 96,
    "<f6>": 97,
    "<f7>": 98,
    "<f8>": 100,
    "<f9>": 101,
    "<f10>": 109,
    "<f11>": 103,
    "<f12>": 111,
    "<up>": 126,
    "<down>": 125,
    "<left>": 123,
    "<right>": 124,
    "<space>": 49,
    "<enter>": 36,
    "<esc>": 53,
    "<tab>": 48,
    "<backspace>": 51,
    "<home>": 115,
    "<end>": 119,
    "<page_up>": 116,
    "<page_down>": 121,
}


def _parse_macos_hotkey(hotkey_str):
    parts = hotkey_str.split("+")
    mods, key, use_keycode = 0, None, False

    for p in parts:
        if p in _PYNPUT_MOD_TO_NS:
            mods |= _PYNPUT_MOD_TO_NS[p]
        elif p in _PYNPUT_KEY_TO_CODE:
            key = _PYNPUT_KEY_TO_CODE[p]
            use_keycode = True
        else:
            key = p.strip("<>").lower()
            use_keycode = False
    return mods, key, use_keycode


_macos_monitor = None
_macos_local_monitor = None
_macos_bindings = []
_macos_lock = threading.Lock()
_gcd_lib = None
_gcd_cb = None
_pending_map = None


def _macos_global_handler(event):
    flags = event.modifierFlags() & _NS_MOD_MASK
    keycode = event.keyCode()
    raw = event.charactersIgnoringModifiers()
    char = raw.lower() if raw else ""
    for mods, key, use_keycode, callback in _macos_bindings:
        if flags == mods:
            if use_keycode and keycode == key:
                threading.Thread(target=callback, daemon=True).start()
                break
            elif not use_keycode and char == key:
                threading.Thread(target=callback, daemon=True).start()
                break


def _macos_local_handler(event):
    flags = event.modifierFlags() & _NS_MOD_MASK
    keycode = event.keyCode()
    raw = event.charactersIgnoringModifiers()
    char = raw.lower() if raw else ""
    for mods, key, use_keycode, callback in _macos_bindings:
        if flags == mods:
            if use_keycode and keycode == key:
                threading.Thread(target=callback, daemon=True).start()
                return None
            elif not use_keycode and char == key:
                threading.Thread(target=callback, daemon=True).start()
                return None
    return event


def _do_rebuild_macos(_ctx):
    """Runs on the main thread via GCD - Registers the NSEvent monitor"""
    global _macos_monitor, _macos_local_monitor, _macos_bindings
    with _macos_lock:
        if _macos_monitor is not None:
            try:
                NSEvent.removeMonitor_(_macos_monitor)
            except Exception:
                pass
            _macos_monitor = None
        if _macos_local_monitor is not None:
            try:
                NSEvent.removeMonitor_(_macos_local_monitor)
            except Exception:
                pass
            _macos_local_monitor = None
        _macos_bindings = []

        if not _pending_map:
            return

        for hotkey_str, callback in _pending_map.items():
            mods, key, use_keycode = _parse_macos_hotkey(hotkey_str)
            if key is not None:
                _macos_bindings.append((mods, key, use_keycode, callback))

        if not _macos_bindings:
            return

        try:
            _macos_monitor = NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
                _NS_KEY_DOWN, _macos_global_handler
            )
            _macos_local_monitor = (
                NSEvent.addLocalMonitorForEventsMatchingMask_handler_(
                    _NS_KEY_DOWN, _macos_local_handler
                )
            )
        except Exception as e:
            print(f"[hotkeys] Failed to register macOS monitor: {e}")


def _dispatch_rebuild_macos(hotkey_map):
    global _pending_map, _gcd_lib, _gcd_cb
    _pending_map = hotkey_map
    if _gcd_lib is None:
        _gcd_lib = ctypes.CDLL("/usr/lib/system/libdispatch.dylib")
        _gcd_lib.dispatch_async_f.argtypes = [
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.CFUNCTYPE(None, ctypes.c_void_p),
        ]
        _gcd_lib.dispatch_async_f.restype = None
    _CB = ctypes.CFUNCTYPE(None, ctypes.c_void_p)
    _gcd_cb = _CB(_do_rebuild_macos)
    main_q = ctypes.addressof(ctypes.c_char.in_dll(_gcd_lib, "_dispatch_main_q"))
    _gcd_lib.dispatch_async_f(main_q, None, _gcd_cb)


hotkey_listener = None
hotkey_lock = threading.Lock()


def increment_hunt_by_id(hunt_id: str) -> None:
    print(f"[hotkeys] Increment fired for {hunt_id}")
    hunts = load_hunts()
    for h in hunts:
        if h["id"] == hunt_id:
            h["count"] += 1
            save_hunts(hunts)
            broadcast(hunts, load_overlays())
            return


def decrement_hunt_by_id(hunt_id: str) -> None:
    print(f"[hotkeys] Decrement fired for {hunt_id}")
    hunts = load_hunts()
    for h in hunts:
        if h["id"] == hunt_id:
            h["count"] = max(0, h["count"] - 1)
            save_hunts(hunts)
            broadcast(hunts, load_overlays())
            return


def rebuild_hotkeys() -> None:
    global hotkey_listener
    hunts = load_hunts()
    active_hunts = [h for h in hunts if h.get("status", "active") == "active"]
    hotkey_map = {}

    for h in active_hunts:
        if h.get("hotkey"):
            hotkey_map[h["hotkey"]] = lambda hid=h["id"]: increment_hunt_by_id(hid)
        if h.get("hotkeyDecrement"):
            hotkey_map[h["hotkeyDecrement"]] = lambda hid=h["id"]: decrement_hunt_by_id(
                hid
            )

    print(f"[hotkeys] Registering: {list(hotkey_map.keys())}")

    if MACOS_AVAILABLE:
        _dispatch_rebuild_macos(hotkey_map)
        return

    if not PYNPUT_AVAILABLE:
        return

    with hotkey_lock:
        if hotkey_listener is not None:
            try:
                hotkey_listener.stop()
            except Exception:
                pass
            hotkey_listener = None

        if not hotkey_map:
            return

        try:
            listener = pynput_keyboard.GlobalHotKeys(hotkey_map)
            listener.daemon = True
            listener.start()
            hotkey_listener = listener
        except Exception as e:
            print(f"[hotkeys] Failed to start listener: {e}")
