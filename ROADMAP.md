# Shiny Trak Roadmap

This document outlines the planned development path for Shiny Trak. Each version is designed to be a self-contained, and meaningful release that builds on the last.  

Progress on each version can be tracked via [GitHub Milestones](https://github.com/Codenii/shiny-trak/milestones).  

---

## Current Release - v1.4.0
Current public release.  
**Core Features:**  
- Track multiple concurrent shiny hunts
- Real-time OBS browser source overlay
- Global hotkeys (Windows/Linux via pynput, macOS via AppKit and PyObjC)
- Pokemon auto-complete with shiny sprites provided by [PokeAPI](https://pokeapi.co)
- System tray / menu bar icon
- Native desktop window via PyWebView (no longer need to use a separate browser tab)
- Full UI overhaul using Alpine.js and Tailwind CSS
- Improved layout, animations, and overall polish
- Add a game field to each hunt
- Active / completed status with the ability to mark a hunt as found/finished
- Start date and end date for time tracking of each individual hunt
- Hunt notes, not shown on the overlay. Used as way to provide personal notes/information on a specific hunt
- Export hunt history to CSV or JSON
- Multiple named overlays, each with their own unique URL
- Assign any hunt to any overlay (or to multiple overlays at the same time)
- Show/hide individual hunts per overlay on demand
- Encounter rate / odds chance display as an optional overlay element
- Full backend unit test suite (pytest)
- Full E2E test suite (pytest-playwright)
- GitHub Actions CI running both suites on Ubuntu, Windows, and macOS
- Total completed hunt count
- Per-game hunt breakdowns
- Statistics overlays (total hunts, game-specific totals)
- Milestone alerts at shiny odds multiples (1x, 2x, 3x base rate)

---

## Upcoming Releases

### v1.4.1 - UI Polish
Update and improve the overall UI of the application
- Remove white card borders
- Audit and improve overal visual consistency

### v1.4.2 - Code Quality
Improvements to the overall code quality of the application and test suite
- Add data-* attribute to templates where needed
- Audit existing E2E selectors
- Identify and resolve/fix any tests that pass by coincidence
- Add input validation for overlay elements schema
- Remove auto-creation of 'main' overlay on startup and update test accordingly
- Add overlay picker when creating a new hunt

### v1.4.3 - Data Management
Give users full control over their hunt data - import, retroactive editing, and custom game support.
- Import hunt data from a JSON or CSV file
- Edit start date on active and completed hunts
- Edit end date on completed hunts
- Edit encounter count on completed hunts
- Create a hunt as already completed at creation time, with optional manual start date, end date, encounters count, and game selection
- Custom game support (for rom hack support) - persists in settings, full Pokemon list autocomplete, PokeAPI optional (graceful no-sprite fallback for custom games)

### v2.0.0 - Overlay Studio
Deep overlay customization.
- Custom CSS editor per overlay, with a live preview
- Expanded display options (ability to choose exactly what each overlay shows)
- More layout and style controls
- Custom sprite support - upload a local image for any hunt, stored in data/sprites/ and served via the app (works in OBS overlay)

### v2.1.0 - OBS Integration
Tighter integration with OBS beyond just being a simple browser source.
- OBS WebSocket support
- Automatic scene switching on events (shiny found, milestones hit, etc.)
- Connection status indicator in the control panel

### v3.0.0 - Shiny Share *(Tentative)*
An optional web platform for sharing hunt history and statistics publicly.
- Opt-in cloud sync - Shiny Trak works completely without it
- Public hunt profile pages
- Share individual hunts or your full history with others

> **Note:** Shiny Share is the most speculative item on this roadmap. It represents a significant scope expansion, and will only be pursued if the rest of the application is in a solid, stable state.

---

## Completed
- **v1.0.0** - Initial Release
- **v1.0.1** - GitHub Actions build automation
- **v1.0.2** - macOS bundle fix
- **v1.0.3** - Switched to Rumps for macOS menu bar
- **v1.0.4** - Further macOS bundle fixes
- **v1.0.5** - Disabled pynput on macOS to resolve crash on hotkey setup
- **v1.1.0** - Native desktop window via PyWebView, full UI overhaul
- **v1.2.0** - Game field, hunt history, mark as found, CSV/JSON export
- **v1.3.0** - Overlay System
- **v1.3.1** - Testing and CI
- **v1.4.0** - Statistics