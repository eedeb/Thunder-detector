#!/usr/bin/env python3
"""
Thunder detector for the LS YMCA (Lampeter).

Thunder can typically be heard up to about 10 miles (~16 km) away. So to decide
whether thunder "would be audible in Lampeter" we check the weather at Lampeter
itself plus a ring of points ~16 km out in every direction. If a thunderstorm is
reported at any of those points, thunder is within earshot and we log the time.

Data source: Open-Meteo (free, no API key required).

The log lives in thunder-log.json and is served by the static site. This script
only rewrites that file when something actually changes (a new thunder episode,
or the daily reset), so the git history stays clean.
"""

import copy
import json
import math
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# --- Configuration -----------------------------------------------------------
# Lampeter, Pennsylvania (Lampeter-Strasburg area). If your YMCA is elsewhere,
# just change these four values.
LOCATION_NAME = "Lampeter, PA"
LATITUDE = 40.0245
LONGITUDE = -76.2444
TIMEZONE = "America/New_York"

# Thunder is audible up to roughly this far away.
AUDIBLE_RADIUS_KM = 16.0

# If a new detection is within this many minutes of the last one, we treat it as
# the same rumbling storm (extend the episode) rather than starting a new entry.
EPISODE_GAP_MINUTES = 25

# WMO weather codes that mean "thunderstorm" in the Open-Meteo API.
THUNDER_CODES = {95, 96, 99}

LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "thunder-log.json")
# -----------------------------------------------------------------------------


def check_points():
    """Lampeter plus 8 compass points on a ring at the audible radius."""
    points = [(LATITUDE, LONGITUDE)]
    dlat = AUDIBLE_RADIUS_KM / 111.0
    dlon = AUDIBLE_RADIUS_KM / (111.0 * math.cos(math.radians(LATITUDE)))
    for bearing in range(0, 360, 45):  # N, NE, E, SE, S, SW, W, NW
        rad = math.radians(bearing)
        points.append((LATITUDE + dlat * math.cos(rad),
                       LONGITUDE + dlon * math.sin(rad)))
    return points


def fetch_weather_codes(points):
    """Return the current WMO weather code for each point (one API call)."""
    lats = ",".join(f"{lat:.4f}" for lat, _ in points)
    lons = ",".join(f"{lon:.4f}" for _, lon in points)
    query = urllib.parse.urlencode({
        "latitude": lats,
        "longitude": lons,
        "current": "weather_code",
        "timezone": TIMEZONE,
    })
    url = f"https://api.open-meteo.com/v1/forecast?{query}"
    with urllib.request.urlopen(url, timeout=30) as resp:
        data = json.load(resp)

    # Open-Meteo returns a single object for one location, a list for many.
    if isinstance(data, dict):
        data = [data]
    return [entry.get("current", {}).get("weather_code") for entry in data]


def load_log():
    try:
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def to_minutes(hhmm):
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def main():
    now = datetime.now(ZoneInfo(TIMEZONE))
    today = now.strftime("%Y-%m-%d")
    now_hhmm = now.strftime("%H:%M")

    log = load_log()

    # Snapshot the old state *before* any mutation, so we can tell whether we
    # actually changed anything and only commit when we did.
    old_state = {
        "location": log.get("location"),
        "date": log.get("date"),
        "entries": copy.deepcopy(log.get("entries", [])),
    }

    entries = log.get("entries", [])

    # Fresh log for a new day.
    if log.get("date") != today:
        entries = []

    # Did we detect thunder within earshot right now?
    try:
        codes = fetch_weather_codes(check_points())
    except Exception as exc:  # network hiccup — skip this run, don't crash
        print(f"Weather lookup failed, skipping run: {exc}", file=sys.stderr)
        # Still perform a daily reset if needed.
        if log.get("date") == today:
            return
        codes = []

    thunder_now = any(code in THUNDER_CODES for code in codes if code is not None)

    if thunder_now:
        if entries:
            last = entries[-1]
            gap = to_minutes(now_hhmm) - to_minutes(last["last"])
            if 0 <= gap <= EPISODE_GAP_MINUTES:
                last["last"] = now_hhmm          # same storm, extend it
            else:
                entries.append({"start": now_hhmm, "last": now_hhmm})
        else:
            entries.append({"start": now_hhmm, "last": now_hhmm})

    new_state = {
        "location": LOCATION_NAME,
        "date": today,
        "entries": entries,
    }

    # Only rewrite the file when the meaningful content changed.
    if new_state == old_state:
        print("No change.")
        return

    output = dict(new_state)
    output["updated"] = now.isoformat(timespec="seconds")
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
        f.write("\n")
    print(f"Log updated ({'thunder logged' if thunder_now else 'daily reset'}).")


if __name__ == "__main__":
    main()
