# Shiny Trak Roadmap

This document outlines the planned development path for Shiny Trak. Each version is designed to be a self-contained, and meaningful release that builds on the last.  

Progress on each version can be tracked via [GitHub Milestones](https://github.com/Codenii/shiny-trak/milestones).  

---

## Current Release - v1.1.0
Current public release.  
**Core Features:**  
- Multiple concurrent shiny tracking
- Real-time OBS browser source overlay
- Global hotkeys (Windows/Linux via pynput, macOS via Hammerspoon)
- Pokemon auto-complete with shiny sprites provided by [PokeAPI](https://pokeapi.co)
- System tray / menu bar icon
- Native desktop window via PyWebView (no longer need to use a separate browser tab)
- Full UI overhaul using Alpine.js and Tailwind CSS
- Improved layout, animations, and overall polish

---

## Upcoming Releases

### v1.2.0 - Hunt History
Hunts become more in-depth and completed hunts are preserved rather than deleted.
- Add a game field to each hunt
- Active / completed status with the ability to mark a hunt as found/finished
- Start date and end date for time tracking of each individual hunt
- Hunt notes, not shown on the overlay. Used as way to provide personal notes/information on a specific hunt
- Export hunt history to CSV or JSON

### v1.3.0 - Overlay System
Full control over what appears in OBS.
- Multiple named overlays, each with their own unique URL
- Assign any hunt to any overlay (or to multiple overlays at the same time)
- Show/hide individual hunts per overlay on demand
- Encounter rate / odds chance display as an optional overlay element

### v1.4.0 - Statistics
Track your progress across all hunts.
- Total completed hunt count
- Per-game hunt breakdowns
- Statistics overlays (total hunts, game-specific totals)
- Milestone alerts at shiny odds multiples (1x, 2x, 3x base rate)

### v2.0.0 - Overlay Studio
Deep overlay customization.
- Custom CSS editor per overlay, with a live preview
- Expanded display options (ability to choose exactly what each overlay shows)
- More layout and style controls

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
