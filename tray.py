import ctypes
import os
import platform
import threading
import time

from store import load_settings


try:
    import webview

    WEBVIEW_AVAILABLE = True
except ImportError:
    WEBVIEW_AVAILABLE = False
    print("[webview] pywebview is not available - falling back to browser mode")

_webview_window = None
_macos_tray_refs = {}
_quitting = False


def _make_tray_icon():
    from PIL import Image, ImageDraw

    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    ImageDraw.Draw(img).ellipse([2, 2, 62, 62], fill=(114, 9, 183, 255))
    return img


def _setup_tray_pystray(window):
    try:
        import pystray

        def _open(icon, item):
            window.show()

        def _quit(icon, item):
            icon.stop()
            os._exit(0)

        icon = pystray.Icon(
            "ShinyTrak",
            _make_tray_icon(),
            "ShinyTrak",
            menu=pystray.Menu(
                pystray.MenuItem("Open Shiny Trak", _open),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Quit", _quit),
            ),
        )
        icon.run_detached()
    except ImportError:
        pass


def _create_macos_status_item(window):
    try:
        from AppKit import (
            NSStatusBar,
            NSMenu,
            NSMenuItem,
            NSVariableStatusItemLength,
            NSObject,
        )

        class _MenuDelegate(NSObject):
            def openApp_(self, sender):
                window.show()

            def quitApp_(self, sender):
                os._exit(0)

        delegate = _MenuDelegate.alloc().init()
        bar = NSStatusBar.systemStatusBar()
        status_item = bar.statusItemWithLength_(NSVariableStatusItemLength)
        status_item.button().setTitle_("✨")

        menu = NSMenu.alloc().init()
        open_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Open Shiny Trak", "openApp:", ""
        )
        open_item.setTarget_(delegate)
        sep = NSMenuItem.separatorItem()
        quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Quit", "quitApp:", ""
        )
        quit_item.setTarget_(delegate)
        for item in [open_item, sep, quit_item]:
            menu.addItem_(item)
        status_item.setMenu_(menu)

        _macos_tray_refs["status_item"] = status_item
        _macos_tray_refs["delegate"] = delegate
        _macos_tray_refs["menu"] = menu
    except Exception as e:
        print(f"[tray] macOS status item failed: {e}")


def _setup_tray(window):
    if platform.system() == "Darwin":
        _lib = ctypes.CDLL("/usr/lib/system/libdispatch.dylib")
        _CB = ctypes.CFUNCTYPE(None, ctypes.c_void_p)
        _cb = _CB(lambda _: _create_macos_status_item(window))
        _macos_tray_refs["_dispatch_cb"] = _cb
        _lib.dispatch_async_f.argtypes = [ctypes.c_void_p, ctypes.c_void_p, _CB]
        _lib.dispatch_async_f.restype = None
        _main_q = ctypes.addressof(ctypes.c_char.in_dll(_lib, "_dispatch_main_q"))
        _lib.dispatch_async_f(_main_q, None, _cb)
    else:
        _setup_tray_pystray(window)


def _on_closing():
    if not _webview_window:
        return
    if _quitting:
        return
    behavior = load_settings().get("close_behavior", "ask")
    if behavior == "minimize":
        _webview_window.hide()
        return False
    elif behavior == "ask":

        def _dispatch():
            time.sleep(0.1)
            if _webview_window:
                _webview_window.evaluate_js(
                    "window.dispatchEvent(new CustomEvent('show-close-dialog'))"
                )

        threading.Thread(target=_dispatch, daemon=True).start()
        return False


def _wait_for_server(port=3000, timeout=10):
    import socket

    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return
        except OSError:
            time.sleep(0.05)
