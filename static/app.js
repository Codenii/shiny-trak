function app() {
  return {
    activeTab: "hunts",
    hunts: [],
    pokemonNames: [],
    acOptions: [],
    games: [],
    gamePokemonNames: [],
    overlays: [],
    selectedOverlayId: null,
    newOverlayName: "",
    showNewOverlay: false,
    showMarkFound: false,
    markFoundHunt: null,
    markFoundNotes: "",
    showExport: false,
    acHighlight: -1,
    newHunt: { name: "", game: "", error: "", loading: false },
    capture: { huntId: null, field: null },
    settings: { close_behavior: "ask", mark_found_behavior: "ask" },
    showCloseDialog: false,
    showSettings: false,
    overlayUrlCopied: false,
    exportScope: "all",
    exportFormat: "json",
    exportMessage: "",
    overlaySubTab: "hunt",
    milestoneAlert: null,
    _milestoneTimer: null,
    _captureListener: null,

    // Lifecycle
    async init() {
      const s = await fetch("/api/settings").then((r) => r.json());
      this.settings = { ...this.settings, ...s };
      fetch("/api/pokemon-list")
        .then((r) => r.json())
        .then((names) => {
          this.pokemonNames = names;
        });
      fetch("/api/games")
        .then((r) => r.json())
        .then((games) => {
          this.games = games;
        });
      this.connect();
      window.addEventListener("show-close-dialog", () => {
        this.showCloseDialog = true;
      });
    },

    connect() {
      const es = new EventSource("/events");
      es.onmessage = (e) => {
        const data = JSON.parse(e.data);
        if (data.hunts) this.hunts = data.hunts;
        if (data.overlays) this.overlays = data.overlays;
      };
      es.addEventListener("milestone", (e) => {
        const data = JSON.parse(e.data);
        this.milestoneAlert = data;
        clearTimeout(this._milestoneTimer);
        this._milestoneTimer = setTimeout(() => {
          this.milestoneAlert = null;
        }, 5000);
      });
      es.onerror = () => {
        es.close();
        setTimeout(() => this.connect(), 3000);
      };
    },

    // Autocomplete
    updateAutocomplete() {
      const q = this.newHunt.name.toLowerCase().trim();
      if (!q) {
        this.acOptions = [];
        this.acHighlight = -1;
        return;
      }
      const list =
        this.newHunt.game && this.gamePokemonNames.length
          ? this.gamePokemonNames
          : this.pokemonNames;
      this.acOptions = list.filter((n) => n.startsWith(q)).slice(0, 8);
      this.acHighlight = -1;
    },

    async onGameChange() {
      this.gamePokemonNames = [];
      this.acOptions = [];
      if (!this.newHunt.game) return;
      const result = await fetch(
        `/api/pokemon-list/game/${encodeURIComponent(this.newHunt.game)}`,
      ).then((r) => r.json());
      if (Array.isArray(result)) this.gamePokemonNames = result;
    },

    selectAc(option) {
      this.newHunt.name = option;
      this.acOptions = [];
      this.acHighlight = -1;
    },

    // Hunt operations
    async addHunt() {
      const name = this.newHunt.name.trim();
      if (!name) return;
      this.newHunt.loading = true;
      this.newHunt.error = "";
      try {
        const pokemon = await fetch(`/api/pokemon/${encodeURIComponent(name)}`).then(
          (r) => r.json(),
        );
        if (pokemon.error) {
          this.newHunt.error = pokemon.error;
          return;
        }
        await fetch("/api/hunts", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            pokemon: pokemon.pokemon,
            displayName: pokemon.displayName,
            spriteUrl: pokemon.spriteUrl,
            game: this.newHunt.game || null,
          }),
        });
        this.newHunt.name = "";
        this.acOptions = [];
      } catch {
        this.newHunt.error = "Failed to add hunt";
      } finally {
        this.newHunt.loading = false;
      }
    },

    async deleteHunt(id) {
      await fetch(`/api/hunts/${id}`, { method: "DELETE" });
    },

    async resetHunt(id) {
      await fetch(`/api/hunts/${id}/reset`, { method: "POST" });
    },

    markFound(hunt) {
      const behavior = this.settings.mark_found_behavior;
      if (behavior === "never") {
        fetch(`/api/hunts/${hunt.id}/complete`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
        });
        return;
      }
      this.markFoundHunt = hunt;
      this.markFoundNotes = hunt.notes || "";
      this.showMarkFound = true;
    },

    async confirmMarkFound() {
      if (!this.markFoundHunt) return;
      await fetch(`/api/hunts/${this.markFoundHunt.id}/complete`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ notes: this.markFoundNotes }),
      });
      this.showMarkFound = false;
      this.markFoundHunt = null;
      this.markFoundNotes = "";
    },

    async updateGame(id, value) {
      fetch(`/api/hunts/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ game: value || null }),
      })
        .then((r) => r.json())
        .then((hunt) => {
          const i = this.hunts.findIndex((h) => h.id === id);
          if (i !== -1) this.hunts[i] = hunt;
        });
    },

    async increment(id) {
      await fetch(`/api/hunts/${id}/increment`, { method: "POST" });
    },

    async decrement(id) {
      await fetch(`/api/hunts/${id}/decrement`, { method: "POST" });
    },

    async setCount(id, value) {
      const count = parseInt(value);
      if (isNaN(count)) return;
      await fetch(`/api/hunts/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ count }),
      });
    },

    // Hotkey capture
    startCapture(huntId, field) {
      this.capture = { huntId, field };
      this._captureListener = (e) => this.onCaptureKey(e);
      document.addEventListener("keydown", this._captureListener);
    },

    onCaptureKey(e) {
      e.preventDefault();
      const key = this.keyToPynput(e);
      if (!key) return;
      document.removeEventListener("keydown", this._captureListener);
      this._captureListener = null;
      const { huntId, field } = this.capture;
      this.capture = { huntId: null, field: null };
      fetch(`/api/hunts/${huntId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ [field]: key }),
      });
    },

    cancelCapture() {
      if (this._captureListener) {
        document.removeEventListener("keydown", this._captureListener);
        this._captureListener = null;
      }
      this.capture = { huntId: null, field: null };
    },

    clearHotkey(id, field) {
      fetch(`/api/hunts/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ [field]: null }),
      });
    },

    keyToPynput(e) {
      const SPECIAL = {
        F1: "<f1>",
        F2: "<f2>",
        F3: "<f3>",
        F4: "<f4>",
        F5: "<f5>",
        F6: "<f6>",
        F7: "<f7>",
        F8: "<f8>",
        F9: "<f9>",
        F10: "<f10>",
        F11: "<f11>",
        F12: "<f12>",
        ArrowUp: "<up>",
        ArrowDown: "<down>",
        ArrowLeft: "<left>",
        ArrowRight: "<right>",
        Enter: "<enter>",
        Escape: "<esc>",
        " ": "<space>",
        Tab: "<tab>",
        Backspace: "<backspace>",
        Delete: "<delete>",
        Insert: "<insert>",
        Home: "<home>",
        End: "<end>",
        PageUp: "<page_up>",
        PageDown: "<page_down>",
      };
      if (["Control", "Shift", "Alt", "Meta"].includes(e.key)) return null;
      const mods = [];
      if (e.ctrlKey) mods.push("<ctrl>");
      if (e.shiftKey) mods.push("<shift>");
      if (e.altKey) mods.push("<alt>");
      if (e.metaKey) mods.push("<cmd>");
      const key = SPECIAL[e.key] || e.key.toLowerCase();
      return [...mods, key].join("+");
    },

    formatHotkey(hotkey) {
      if (!hotkey) return "";
      const MAP = {
        "<ctrl>": "Ctrl",
        "<shift>": "Shift",
        "<alt>": "Alt",
        "<cmd>": "Cmd",
        "<f1>": "F1",
        "<f2>": "F2",
        "<f3>": "F3",
        "<f4>": "F4",
        "<f5>": "F5",
        "<f6>": "F6",
        "<f7>": "F7",
        "<f8>": "F8",
        "<f9>": "F9",
        "<f10>": "F10",
        "<f11>": "F11",
        "<f12>": "F12",
        "<up>": "↑",
        "<down>": "↓",
        "<left>": "←",
        "<right>": "→",
        "<enter>": "Enter",
        "<esc>": "Esc",
        "<space>": "Space",
        "<tab>": "Tab",
        "<backspace>": "Backspace",
        "<delete>": "Delete",
        "<insert>": "Insert",
        "<home>": "Home",
        "<end>": "End",
        "<page_up>": "PgUp",
        "<page_down>": "PgDn",
      };
      return hotkey
        .split("+")
        .map((p) => MAP[p] || p.toUpperCase())
        .join("+");
    },

    // Settings
    async saveSettings() {
      await fetch("/api/settings", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(this.settings),
      });
    },

    // Close Behavior
    async confirmClose(action) {
      this.showCloseDialog = false;
      await fetch("/api/close-action", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action }),
      });
    },

    quit() {
      this.confirmClose("quit");
    },

    async exportHunts(scope, fmt) {
      const result = await fetch(`/api/export?scope=${scope}&format=${fmt}`).then((r) =>
        r.json(),
      );
      if (result.ok) {
        this.exportMessage = `Saved to Downloads/${result.filename}`;
        setTimeout(() => (this.exportMessage = ""), 4000);
      }
      this.showExport = false;
    },

    async addOverlay() {
      if (!this.newOverlayName.trim()) return;
      await fetch("/api/overlays", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: this.newOverlayName.trim(),
          type: this.overlaySubTab,
        }),
      });
      this.newOverlayName = "";
      this.showNewOverlay = false;
    },

    async deleteOverlay(id) {
      await fetch(`/api/overlays/${id}`, { method: "DELETE" });
    },

    async toggleHuntVisibility(overlayId, huntId) {
      const overlay = this.overlays.find((o) => o.id === overlayId);
      if (!overlay) return;
      const existing = overlay.hunts.find((h) => h.huntId === huntId);
      let updatedHunts;
      if (existing) {
        updatedHunts = overlay.hunts.map((h) =>
          h.huntId === huntId ? { ...h, visible: !h.visible } : h,
        );
      } else {
        updatedHunts = [...overlay.hunts, { huntId, visible: true }];
      }
      await fetch(`/api/overlays/${overlayId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ hunts: updatedHunts }),
      });
    },

    async updateOverlayElement(overlayId, element, value) {
      const overlay = this.overlays.find((o) => o.id === overlayId);
      if (!overlay) return;
      const updatedElements = { ...overlay.elements, [element]: value };
      await fetch(`/api/overlays/${overlayId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ elements: updatedElements }),
      });
    },

    async updateOverlayGame(overlayId, game) {
      await fetch(`/api/overlays/${overlayId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ game: game || null }),
      });
    },

    async copyOverlayUrl(overlay) {
      const suffix = overlay.type === "stats" ? "-stats" : "-hunt";
      await navigator.clipboard.writeText(
        `http://localhost:3000/overlay/${overlay.name}${suffix}`,
      );
    },

    async updateEncounterRate(id, value) {
      await fetch(`/api/hunts/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ encounterRate: value ? parseInt(value) : null }),
      });
    },
  };
}
