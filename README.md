# ⛈️ LS YMCA Thunder Log

A little GitHub Pages site that keeps a daily log of thunder for the
**LS YMCA in Lampeter**. Whenever thunder would be audible in Lampeter — that
is, whenever a thunderstorm is within about **10 miles (16 km)** — the time gets
written to a log that anyone can see. The log starts fresh every day.

## How it works

GitHub Pages only serves static files, so the detection and logging happen in a
**scheduled GitHub Action** instead of in the page:

1. `.github/workflows/thunder.yml` runs `scripts/check_thunder.py` **every 10
   minutes**.
2. The script asks the free [Open-Meteo](https://open-meteo.com/) API for the
   current weather at Lampeter **and at a ring of points ~16 km out** in every
   direction. If any of them reports a thunderstorm, thunder is within earshot.
3. When thunder is detected, the time is appended to `thunder-log.json`. Nearby
   detections are grouped into a single episode (e.g. `2:32 PM – 3:10 PM`).
4. At the start of each new day (America/New_York) the log resets automatically.
5. `index.html` reads `thunder-log.json` and displays today's log, refreshing
   itself once a minute.

The workflow only commits when the log actually changes, so history stays tidy.

## One-time setup

1. **Push this repo to GitHub.**
2. **Enable GitHub Pages:** repo **Settings → Pages → Build and deployment →
   Source: Deploy from a branch**, branch **`main`**, folder **`/ (root)`**.
   Your site will be at `https://<username>.github.io/<repo>/`.
3. **Allow the Action to commit:** repo **Settings → Actions → General →
   Workflow permissions → Read and write permissions**. (The workflow already
   requests this, but the repo setting must allow it too.)
4. The schedule starts on its own. To test immediately, open the **Actions**
   tab, pick **Thunder watch**, and click **Run workflow**.

## Changing the location

Everything is driven by four values at the top of
[`scripts/check_thunder.py`](scripts/check_thunder.py):

```python
LOCATION_NAME = "Lampeter, PA"
LATITUDE = 40.0245
LONGITUDE = -76.2444
TIMEZONE = "America/New_York"
```

Update those (and `TIMEZONE` in `app.js` to match) if your YMCA is somewhere
else — for example Lampeter, Wales.

## Notes

- GitHub's scheduled workflows can be delayed by a few minutes under load, and
  the minimum interval is 5 minutes — so a very brief thunderclap between checks
  could be missed. For a YMCA safety log this is normally fine, but it is not a
  substitute for an official lightning-detection system.
- Thunderstorm detection uses WMO weather codes `95`, `96`, and `99`.
