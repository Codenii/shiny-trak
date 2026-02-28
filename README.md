# Shiny Trak

A local web-based shiny Pokemon hunt counter with a real-time OBS overlay. Has to ability to track multiple hunts simultaneously, configurable per-hunt display modes, and increment counters via global hotkeys without leaving the game.

## Features

- Track multiple concurrent shiny hunts
- Three display modes per hunt: counter only, name + counter, and sprite + name + counter
- Real-time OBS browser source overlay
- Global hotkeys for increment and decrement (no app focus needed)
- Auto-complete Pokemon name search with shiny sprites from PokeAPI

---

## Requirements

- Python 3.8+
- pip

---

## Installation

### 1. Install dependencies
**Windows**
```pip install -r requirements.txt```

**macOS / Linux**
```pip3 install -r requirements.txt```

### 2. Start the server

**Windows**
```python app.py```

**macOS / Linux**
```python3 app.py```

The server runs at `http://localhost:3000`.

---

## Usage

### Control Panel
Open `http://localhost:3000` in your web browser.

- **Add Hunt**: Type a pokemon name in the search box and select a display mode. Then click **Add Hunt**
- **+ / -**: Increment or decrement the counter
- **Reset**: Set the counter back to zero
- **Delete**: Remove the hunt from the tracker completely
- **Display mode**: Change how the hunt appears on the overlay (Full / Name / Counter)
- **Hotkeys**: Assign global keyboard shortcuts to increment/decrement each hunt (see below)

### OBS Overlay
In OBS, add a **Browser Source** with the following settings:

| Setting | Value |
|---|---|
| URL | `http://localhost:3000/overlay` |
| Width | 400 (or whatever fits your layout) |
| Height | 300 (or whatever fits your layout) |
| Shutdown source when not visible | Unchecked |
| Refresh browser when scene becomes active | Unchecked |

The overlay has a transparent background and will update instantly whenever you increment a counter.

---

## Hotkeys

### Windows and Linux

Hotkeys work out of the box via pynput. In the control panel, click **Set** next to a hunt and press any key combination. The hotkey will fire globally even when the app is not focused.

> **Note for Linux users**: pynput may require you to run app as root, or add your user to the 'input' group:
> ```
> sudo usermod -aG input $USER
> ```
> Log out and back in for the changes to take effect.

### macOS - Hammerspoon

Due to macOS security restrictions, global hotkeys require [Hammerspoon](https://www.hammerspoon.org), a free macOS automation tool.

**Setup:**

1. Download and install Hammerspoon from [hammerspoon.org](https://www.hammerspoon.org)
2. Launch Hammerspoon and click **Open Config** from the menu bar icon
3. In the control panel, assign hotkeys to your hunts using the **Set** buttons
4. Open `http://localhost:3000/api/hammerspoon` in your browser - this generates a Lua config file
5. Copy the entire contents and paste them into your Hammerspoon config file
6. Click **Reload Config** in the Hammerspoon menu bar icon

Repeat steps 4-6 any time you add, remove, or change a hotkey.

---

## Data

Hunt data is saved automatically to `data/hunts.json`. This file is created on first run. Back it up if you want to preserve your counts.

---

## Troubleshooting

**PokeAPI lookups fail / no sprite loads**
The app fetches Pokemon data from [pokeapi.co](https://pokeapi.co). Check your internet connection. The Pokemon list is cached after the first successful fetch.

**Hotkeys not firing on Windows**
Make sure no other application has registered the same key combination. Function keys (F1-F12) are recommended to avoid conflicts.

**Overlay shows blank in OBS**
Ensure the server is running before OBS loads the browser source. If it was added while the server was stopped, click **Refresh** on the browser source.

**Port 3000 already in use**
Edit the last line of `app.py` and change the port number:
```python
app.run(host="0.0.0.0", port=3000, threaded=True)
```
Remember to update the OBS browser source URL to match the new port.