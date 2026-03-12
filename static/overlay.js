let prevCounts = {};

function renderOverlay(hunts, overlays) {
  const overlay = overlays.find((o) => o.id === OVERLAY_ID);
  if (!overlay) return;

  if (overlay.type === 'stats') {
    renderStats(hunts, overlay);
  } else {
    renderHunts(hunts, overlay);
  }
}

function renderStats(hunts, overlay) {
  const container = document.getElementById('hunts');
  container.innerHTML = '';

  const game = overlay.game || null;
  const filtered = game ? hunts.filter((h) => h.game === game) : hunts;
  const completed = filtered.filter((h) => h.status === 'completed');
  const active = filtered.filter((h) => h.status === 'active' || !h.status);
  const totalCompleted = hunts.filter((h) => h.status === 'completed').length;

  if (overlay.elements.totalCompleted) {
    const total = document.createElement('div');
    total.className = 'stat-line';
    total.textContent = `Total Completed: ${totalCompleted} hunt${completed.length !== 1 ? 's' : ''}`;
    container.appendChild(total);
  }

  if (overlay.elements.breakdown === 'completed') {
    const line = document.createElement('div');
    line.className = 'stat-line';
    line.textContent = `Completed: ${completed.length} / ${completed.length + active.length} total`;
    container.appendChild(line);
  } else if (overlay.elements.breakdown === 'active') {
    const line = document.createElement('div');
    line.className = 'stat-line';
    line.textContent = `Completed: ${completed.length} · Active: ${active.length}`;
    container.appendChild(line);
  }
}

function renderHunts(hunts, overlay) {
  const visibleIds = new Set(
    overlay.hunts.filter((h) => h.visible).map((h) => h.huntId),
  );

  const filtered = hunts.filter(
    (h) => (h.status === "active" || !h.status) && visibleIds.has(h.id),
  );
  const container = document.getElementById("hunts");
  const newCounts = {};
  filtered.forEach((h) => {
    newCounts[h.id] = h.count;
  });

  container.innerHTML = "";

  filtered.forEach((hunt) => {
    const card = document.createElement("div");
    card.className = "hunt-card";

    // Sparkle
    const sparkle = document.createElement("span");
    sparkle.className = "sparkle";
    sparkle.textContent = "✨";
    card.appendChild(sparkle);

    // Sprite (full mode only)
    if (overlay.elements.sprite === true && hunt.spriteUrl) {
      const img = document.createElement("img");
      img.className = "sprite";
      img.src = hunt.spriteUrl;
      img.alt = hunt.displayName;
      img.onerror = () => (img.style.display = "none");
      card.appendChild(img);
    }

    // Name (name + full modes)
    if (overlay.elements.name === true) {
      const name = document.createElement("span");
      name.className = "hunt-name";
      name.textContent = hunt.displayName;
      card.appendChild(name);

      const sep = document.createElement("span");
      sep.className = "separator";
      sep.textContent = "·";
      card.appendChild(sep);
    }

    // Count
    if (overlay.elements.count === true) {
      const countEl = document.createElement("span");
      countEl.className = "hunt-count";
      countEl.textContent = hunt.count.toLocaleString("en-US");

      // Flash animation if count changed
      if (prevCounts[hunt.id] !== undefined && prevCounts[hunt.id] !== hunt.count) {
        countEl.classList.add("count-flash");
        countEl.addEventListener(
          "animationend",
          () => {
            countEl.classList.remove("count-flash");
          },
          { once: true },
        );
      }

      card.appendChild(countEl);
    }

    // Odds
    if (overlay.elements.odds === true && hunt.encounterRate) {
      const sep2 = document.createElement("span");
      sep2.className = "separator";
      sep2.textContent = "·";
      card.appendChild(sep2);

      const oddsEl = document.createElement("span");
      oddsEl.className = "hunt-odds";
      oddsEl.textContent = `1/${hunt.encounterRate.toLocaleString("en-US")}`;
      card.appendChild(oddsEl);
    }
    container.appendChild(card);
  });

  prevCounts = newCounts;
}

function connect() {
  const es = new EventSource("/events");
  es.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data);
      if (data.hunts && data.overlays) renderOverlay(data.hunts, data.overlays);
    } catch (err) {
      console.error("Parse error:", err);
    }
  };
  es.onerror = () => {
    es.close();
    setTimeout(connect, 3000);
  };
}

connect();
