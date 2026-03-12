# Shiny Trak

[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![GitHub release](https://img.shields.io/github/v/release/Codenii/shiny-trak)](https://github.com/Codenii/shiny-trak/releases/latest)
[![CI](https://github.com/Codenii/shiny-trak/actions/workflows/build.yml/badge.svg)](https://github.com/Codenii/shiny-trak/actions/workflows/build.yml)
[![Tests](https://github.com/Codenii/shiny-trak/actions/workflows/test.yml/badge.svg)](https://github.com/Codenii/shiny-trak/actions/workflows/test.yml)
[![Platform](https://img.shields.io/badge/platform-Windows%20|%20macOS%20|%20Linux-blue)](https://github.com/Codenii/shiny-trak/releases/latest)

A local web-based shiny Pokemon hunt tracker with a real-time OBS overlay. Track multiple hunts simultaneously, configure per-hunt display modes, and      
increment counters via global hotkeys without leaving your game.

## Features

- Track multiple concurrent shiny hunts
- Three display modes per hunt: counter only, name + counter, and sprite + name + counter
- Real-time OBS browser source overlay
- Global hotkeys for increment and decrement (no app focus needed)
- Manual count entry for starting a hunt mid-way through
- Auto-complete Pokemon name search with shiny sprites from PokeAPI
- Game field per hunt with game-filtering Pokemon autocomplete
- Mark hunt as found with optional notes field
- Hunt history tab showing completed hunts
- Export hunt data to CSV or JSON

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

**Linux**: Install the required system libraries, then make the file executable, then run it:
`sudo apt-get install -y gir1.2-gtk-3.0 gir1.2-webkit2-4.1`
`chmod +x ShinyTrak
./ShinyTrak`. 
_Note: The Linux build is currently untested on physical hardware. Hotkeys and the system tray may not work depending on your desktop environment_

### Running from Source

Requires Python 3.8+ and pip.

**Windows**
`pip install -r requirements.txt
python app.py`

**macOS / Linux**
`pip3 install -r requirements.txt
python3 app.py`

---

## First Launch on macOS

macOS will block the app on first launch because it is not signed by an Apple-registered developer.

**To open it:**
1. Unzip and move `ShinyTrak.app` to your Applications folder
2. Open Terminal and run:
   `xattr -cr /Applications/ShinyTrak.app`
3. Right-click `ShinyTrak.app` → **Open**
4. Click **Open** in the dialog that appears

You only need to do this once. If that doesn't work, go to **System Settings → Privacy & Security**, scroll down to the blocked app message, and click
**Open Anyway**.

**For hotkeys to work**, you also need to grant Input Monitoring permission:

1. Open **System Settings -> Privacy & Security -> Input Monitoring**
2. Enable the toggle next to **ShinyTrak** (or your terminal app if running from source)

---

## Usage

### Starting and Stopping

When launched, Shiny Trak automatically opens the control panel in your browser. A tray icon appears in your system tray (Windows/macOS; Linux support varies by desktop environment) — right-click it to reopen the control panel or quit.

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
- **Game**: Select which game the hunt is for (filters the Pokemon autocomplete)
- **Mark as Found**: Complete hunts and move them to the history tab
- **Export**: Download hunt data in either CSV or JSON format

### OBS Overlay

In OBS, add a **Browser Source** with the following settings:

| Setting | Value |
|---|---|
| URL | `http://localhost:3000/overlay/<name>-hunt` or `http://localhost:3000/overlay/<name>-stats` |
| Width | 400 (or whatever fits your layout) |
| Height | 300 (or whatever fits your layout) |
| Shutdown source when not visible | Unchecked |
| Refresh browser when scene becomes active | Unchecked |

Replace `<name>` with the name of your overlay. For example, a hunt overlay named "main" would be `http://localhost:3000/overlay/main-hunt`. Whereas a stats overlay named "test" would be `http://localhost:3000/overlay/test-stats`

The overlay has a transparent background and will update instantly whenever you change a counter or your stats update.

> **Upgrading from v1.3.x?** Overlay URLs have changed. Update your OBS browser sources from `/overlay/<name>` to `/overlay/<name>-hunt`. Also note that hunts are no longer automatically added to overlays - you will need to manually assign hunts to each overlay via the Overlays tab.
---

## Hotkeys

### Windows and Linux

Hotkeys work out of the box on Windows. Linux support is untested - hotkeys may require additional setup depending on your desktop environment and input configuration.  
In the control panel, click **Set** next to a hunt and press any key combination. The hotkey will fire globally even when the
app is not focused.

> **Note for Linux users**: pynput may require adding your user to the `input` group:
> ```
> sudo usermod -aG input $USER
> ```
> Log out and back in for the change to take effect.

### macOS

Hotkeys work natively on macOS - no third-party tools required. See [First Launch on macOS](#first-launch-on-macos) for the one-time Input Monitoring permission required.

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

## Development

### Running Tests

**Backend tests:**
`pytest tests/ --ignore=tests/e2e -v`

**E2E tests** (requires Playwright):
`playwright install chromium  
pytest tests/e2e/ -v`

---

## Roadmap
Shiny Trak is actively being developed. Planned features include multiple overlay support, statistics tracking, and more.  

See the full [Roadmap](ROADMAP.md) for details.
