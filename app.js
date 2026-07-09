const TIMEZONE = "America/New_York";
const REFRESH_MS = 60 * 1000; // re-check the log every minute

// Today's date (YYYY-MM-DD) in the YMCA's timezone, so the log clears at local
// midnight even if a viewer is in another timezone.
function localToday() {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: TIMEZONE,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date());
}

// "14:32" -> "2:32 PM"
function pretty(hhmm) {
  const [h, m] = hhmm.split(":").map(Number);
  const period = h >= 12 ? "PM" : "AM";
  const h12 = h % 12 === 0 ? 12 : h % 12;
  return `${h12}:${String(m).padStart(2, "0")} ${period}`;
}

function prettyDate(dateStr) {
  const d = new Date(dateStr + "T00:00:00");
  return d.toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
  });
}

function render(log) {
  const today = localToday();
  const isToday = log && log.date === today;
  const entries = isToday && Array.isArray(log.entries) ? log.entries : [];

  document.getElementById("location").textContent =
    (log && log.location) || "Lampeter";
  document.getElementById("date").textContent = "— " + prettyDate(today);

  const status = document.getElementById("status");
  const statusIcon = document.getElementById("status-icon");
  const statusText = document.getElementById("status-text");
  const list = document.getElementById("entries");
  const empty = document.getElementById("empty");

  list.innerHTML = "";

  if (entries.length === 0) {
    status.className = "status status--quiet";
    statusIcon.textContent = "🔇";
    statusText.textContent = "No thunder heard yet today";
    empty.hidden = false;
  } else {
    empty.hidden = true;
    const count = entries.length;
    status.className = "status status--alert";
    statusIcon.textContent = "🔊";
    statusText.textContent =
      count === 1
        ? "Thunder heard today"
        : `Thunder heard ${count} times today`;

    for (const e of entries) {
      const li = document.createElement("li");
      const range =
        e.last && e.last !== e.start
          ? `${pretty(e.start)} – ${pretty(e.last)}`
          : pretty(e.start);
      li.innerHTML =
        `<span class="bolt">⚡</span>` +
        `<span class="time">${range}</span>`;
      list.appendChild(li);
    }
  }

  const updated = document.getElementById("updated");
  if (isToday && log.updated) {
    updated.textContent = new Date(log.updated).toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
      timeZone: TIMEZONE,
    });
  } else {
    updated.textContent = "—";
  }
}

async function refresh() {
  try {
    // Cache-bust so we always see the latest committed log.
    const res = await fetch(`thunder-log.json?t=${Date.now()}`, {
      cache: "no-store",
    });
    if (!res.ok) throw new Error(res.status);
    render(await res.json());
  } catch (err) {
    document.getElementById("status-text").textContent =
      "Could not load the log right now.";
    console.error("Failed to load thunder log:", err);
  }
}

refresh();
setInterval(refresh, REFRESH_MS);
