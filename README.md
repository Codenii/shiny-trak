# Shiny Trak

A local web-based shiny Pokemon hunt tracker with a real-time OBS overlay. Track multiple hunts simultaneously, configure per-hunt display modes, and      
increment counters via global hotkeys without leaving your game.

## Features

- Track multiple concurrent shiny hunts
- Three display modes per hunt: counter only, name + counter, and sprite + name + counter
- Real-time OBS browser source overlay
- Global hotkeys for increment and decrement (no app focus needed)
- Manual count entry for starting a hunt mid-way through
- Auto-complete Pokemon name search with shiny sprites from PokeAPI

---

## Installation

### Executable (Recommended)

Download the latest release for your platform from the [Releases](../../releases) page:

| Platform | File |
|---|---|
| Windows | `ShinyTrak.exe` |
| macOS | `ShinyTrak.app.zip` |
| Linux | `ShinyTrak` |

**Windows**: Double-click `ShinyTrak.exe`. The control panel will open in your browser automatically.

**macOS**: Unzip and move `ShinyTrak.app` to your Applications folder. See [First Launch on macOS](#first-launch-on-macos) below.

**Linux**: Make the file executable, then run it:
```chmod +x ShinyTrak
./ShinyTrak```

### Running from Source

Requires Python 3.8+ and pip.

**Windows**
```pip install -r requirements.txt
python app.py```

**macOS / Linux**
```pip3 install -r requirements.txt
python3 app.py```

---

## First Launch on macOS

macOS will block the app on first launch because it is not signed by an Apple-registered developer.

**To open it:**
1. Right-click `ShinyTrak.app` → **Open**
2. Click **Open** in the dialog that appears

You only need to do this once. If that doesn't work, go to **System Settings → Privacy & Security**, scroll down to the blocked app message, and click
**Open Anyway**.

---

## Usage

### Starting and Stopping

When launched, Shiny Trak automatically opens the control panel in your browser. A tray icon appears in your system tray (Windows/macOS) — right-click it
to reopen the control panel or quit.

To shut down from the browser, click the **⏻ Shut Down** button at the top of the control panel.

### Control Panel

Open `http://localhost:3000` in your browser.

- **Add Hunt**: Type a Pokemon name, select a display mode, then click **Add Hunt**
- **+ / −**: Increment or decrement the counter
- **Count field**: Click the number and type a value to set the counter manually
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

The overlay has a transparent background and will update instantly whenever you change a counter.

---

## Hotkeys

### Windows and Linux

Hotkeys work out of the box. In the control panel, click **Set** next to a hunt and press any key combination. The hotkey will fire globally even when the
app is not focused.

> **Note for Linux users**: pynput may require adding your user to the `input` group:
> ```
> sudo usermod -aG input $USER
> ```
> Log out and back in for the change to take effect.

### macOS — Hammerspoon

Due to macOS security restrictions, global hotkeys require [Hammerspoon](https://www.hammerspoon.org), a free macOS automation tool.

**Setup:**

1. Download and install Hammerspoon from [hammerspoon.org](https://www.hammerspoon.org)
2. Launch Hammerspoon and click **Open Config** from the menu bar icon
3. In the control panel, assign hotkeys to your hunts using the **Set** buttons
4. Open `http://localhost:3000/api/hammerspoon` in your browser — this generates a Lua config file
5. Copy the entire contents and paste them into your Hammerspoon config file
6. Click **Reload Config** in the Hammerspoon menu bar icon

Repeat steps 4–6 any time you add, remove, or change a hotkey.

---

## Data

Hunt data is saved automatically to a `data/hunts.json` file next to the executable. It is created on first run. Back it up if you want to preserve your
counts between reinstalls.

---

## Troubleshooting

**PokeAPI lookups fail / no sprite loads**
The app fetches Pokemon data from [pokeapi.co](https://pokeapi.co). Check your internet connection. The Pokemon name list is cached after the first
successful fetch.

**Hotkeys not firing on Windows**
Make sure no other application has registered the same key combination. Function keys (F1–F12) are recommended to avoid conflicts.

**Overlay shows blank in OBS**
Ensure Shiny Trak is running before OBS loads the browser source. If the source was added while the app was stopped, click **Refresh** on the browser
source in OBS.

**Port 3000 already in use**
Another application is using port 3000. Quit that application, or if running from source, edit the last line of `app.py` to use a different port and update
the OBS browser source URL to match.