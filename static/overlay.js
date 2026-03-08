let prevCounts = {};

function renderHunts(hunts, overlays) {
  const overlay = overlays.find((o) => o.id === OVERLAY_ID);
  if (!overlay) return;

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
      if (data.hunts && data.overlays) renderHunts(data.hunts, data.overlays);
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
