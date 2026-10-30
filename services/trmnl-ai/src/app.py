"""trmnl-ai: fetch weather + TfL data, ask an LLM (OpenRouter) to design the TRMNL screen as HTML,
serve it at :8080/screen.json for the Terminus poll extension "AI Board".

Stdlib only. Usage:
  python app.py                      # loop forever (fetch every FETCH_EVERY s) + HTTP server
  python app.py --once [--force]     # one fetch/generate cycle, then exit (--force: ignore hash/age)
  python app.py --once --force --data fixture.json   # generate from a fixture instead of live data
  python app.py --once --force --fresh               # new design from prompt.md only (ignore previous screen)
"""
import argparse
import datetime as dt
import hashlib
import http.server
import json
import os
import re
import sys
import threading
import time
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/London")
HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get("DATA_DIR", "/data")
PROMPT_FILE = os.environ.get("PROMPT_FILE", os.path.join(HERE, "prompt.md"))
MODEL = os.environ.get("OPENROUTER_MODEL", "anthropic/claude-haiku-5.5")
API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
FETCH_EVERY = int(os.environ.get("FETCH_EVERY", "300"))  # s between data fetches
MIN_GAP = int(os.environ.get("MIN_GAP", "1200"))  # s: never regenerate more often than this
MAX_AGE = int(os.environ.get("MAX_AGE", "3600"))  # s: regenerate at least this often
QUIET = os.environ.get("QUIET_HOURS", "0-6")  # local hours with no LLM calls (device shows last screen)

SVS, KSX = "940GZZLUSVS", "940GZZLUKSX"  # Seven Sisters, King's Cross St Pancras
LINES = "victoria,piccadilly,central"
WMO = {0: "Clear", 1: "Mostly clear", 2: "Partly cloudy", 3: "Overcast", 45: "Fog", 48: "Fog",
       51: "Light drizzle", 53: "Drizzle", 55: "Heavy drizzle", 56: "Freezing drizzle", 57: "Freezing drizzle",
       61: "Light rain", 63: "Rain", 65: "Heavy rain", 66: "Freezing rain", 67: "Freezing rain",
       71: "Light snow", 73: "Snow", 75: "Heavy snow", 77: "Snow grains", 80: "Light showers",
       81: "Showers", 82: "Heavy showers", 85: "Snow showers", 86: "Snow showers",
       95: "Thunderstorm", 96: "Thunderstorm + hail", 99: "Thunderstorm + hail"}

lock = threading.Lock()


def log(*a):
    print(dt.datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S"), *a, flush=True)


def get_json(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": "trmnl-ai/1 (homelab)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def clean(text, n=220):
    text = re.sub(r"\s+", " ", text or "").strip()
    return text if len(text) <= n else text[: n - 1] + "…"


# ---------- data ----------

def weather(target):
    q = urllib.parse.urlencode({
        "latitude": 51.5829, "longitude": -0.0733, "timezone": "Europe/London", "forecast_days": 2,
        "current": "temperature_2m,apparent_temperature,weather_code,wind_speed_10m",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,"
                 "precipitation_sum,wind_speed_10m_max,sunrise,sunset",
        "hourly": "temperature_2m,precipitation_probability,weather_code"})
    w = get_json("https://api.open-meteo.com/v1/forecast?" + q)
    c, d, h = w["current"], w["daily"], w["hourly"]
    days = [{"date": d["time"][i], "summary": WMO.get(d["weather_code"][i], "?"),
             "max_c": round(d["temperature_2m_max"][i]), "min_c": round(d["temperature_2m_min"][i]),
             "rain_chance_pct": d["precipitation_probability_max"][i], "rain_mm": d["precipitation_sum"][i],
             "wind_max_kmh": round(d["wind_speed_10m_max"][i]),
             "sunrise": d["sunrise"][i][-5:], "sunset": d["sunset"][i][-5:]} for i in range(len(d["time"]))]
    hours = [{"time": t, "temp_c": round(h["temperature_2m"][i]), "rain_pct": h["precipitation_probability"][i],
              "summary": WMO.get(h["weather_code"][i], "?")}
             for i, t in enumerate(h["time"])
             if t.startswith(target.isoformat()) and 6 <= int(t[11:13]) <= 22 and int(t[11:13]) % 2 == 0]
    return {"location": "Seven Sisters, London",
            "now": {"temp_c": round(c["temperature_2m"]), "feels_like_c": round(c["apparent_temperature"]),
                    "summary": WMO.get(c["weather_code"], "?"), "wind_kmh": round(c["wind_speed_10m"])},
            "days": days, "target_day_every_2h": hours}


def line_status(url):
    out = []
    for line in get_json(url):
        sts = [{"status": s["statusSeverityDescription"], "severity": s["statusSeverity"],
                "reason": clean(s.get("reason"), 300) or None,
                "from": (s.get("validityPeriods") or [{}])[0].get("fromDate"),
                "to": (s.get("validityPeriods") or [{}])[0].get("toDate")}
               for s in line["lineStatuses"]]
        out.append({"line": line["name"], "statuses": sts})
    return out


def journey(target, today):
    url = f"https://api.tfl.gov.uk/Journey/JourneyResults/{SVS}/to/{KSX}?mode=tube"
    if target != today:
        url += f"&date={target.strftime('%Y%m%d')}&time=0830&timeIs=Departing"
    js = get_json(url).get("journeys") or []
    if not js:
        return {"found": False}
    j = js[0]
    legs = [{"mode": l["mode"]["id"], "line": (l.get("routeOptions") or [{}])[0].get("name"),
             "summary": l["instruction"]["summary"], "minutes": l["duration"],
             "disruptions": [clean(x.get("description"), 200) for x in l.get("disruptions") or []]}
            for l in j["legs"]]
    return {"found": True, "for": "next departure" if target == today else "tomorrow 08:30",
            "duration_min": j["duration"], "usual_duration_min": 9, "legs": legs}


def station_disruptions():
    out = []
    for d in get_json(f"https://api.tfl.gov.uk/StopPoint/{SVS},{KSX}/Disruption"):
        out.append({"station": d.get("commonName") or d.get("atcoCode"), "type": d.get("type"),
                    "description": clean(d.get("description"), 260),
                    "from": d.get("fromDate"), "to": d.get("toDate")})
    return out


def crowding(naptan, day):
    c = get_json(f"https://api.tfl.gov.uk/crowding/{naptan}/{day}")
    return {"am_peak": c.get("amPeakTimeBand"), "pm_peak": c.get("pmPeakTimeBand")}


def collect():
    now = dt.datetime.now(TZ)
    target = (now + dt.timedelta(hours=2)).date()  # rolls to tomorrow at 22:00, like Morning Board
    today = now.date()
    data = {"generated_for": {"now_local": now.strftime("%a %d %b %Y %H:%M"),
                              "target_day": target.isoformat(),
                              "target_label": "Today" if target == today else "Tomorrow"}}
    window = f"{now.strftime('%Y-%m-%dT%H:%M:%S')}/to/{target.isoformat()}T23:59:59"
    jobs = {
        "weather": lambda: weather(target),
        "lines_now": lambda: line_status(f"https://api.tfl.gov.uk/Line/{LINES}/Status"),
        "lines_planned_until_end_of_target_day":
            lambda: line_status(f"https://api.tfl.gov.uk/Line/{LINES}/Status/{window}"),
        "commute_seven_sisters_to_kings_cross": lambda: journey(target, today),
        "station_disruptions": station_disruptions,
        "crowding_seven_sisters": lambda: crowding(SVS, target.strftime("%a")),
        "crowding_kings_cross": lambda: crowding(KSX, target.strftime("%a")),
    }
    for name, fn in jobs.items():
        try:
            data[name] = fn()
        except Exception as e:  # one bad source must not kill the screen
            data[name] = {"error": f"{type(e).__name__}: {e}"[:200]}
            log("fetch failed", name, data[name]["error"])
    return data


def data_hash(data):
    # Ignore the clock and the noisy hourly temps so we only regenerate on meaningful change;
    # MAX_AGE refreshes the "updated" time and forecast anyway.
    d = dict(data)
    d.pop("generated_for", None)
    w = d.get("weather")
    if isinstance(w, dict) and "days" in w:
        d["weather"] = {"days": w["days"], "now_summary": w["now"]["summary"]}
    d["target_day"] = data["generated_for"]["target_day"]
    return hashlib.sha256(json.dumps(d, sort_keys=True).encode()).hexdigest()[:16]


# ---------- LLM ----------

def llm(data, feedback=None, previous=None):
    prev = ("\n\nPrevious screen (keep its layout, update the content):\n```html\n" + previous + "\n```"
            if previous else "")
    messages = [{"role": "system", "content": open(PROMPT_FILE).read()},
                {"role": "user", "content": "Design the screen for this data:\n```json\n"
                 + json.dumps(data, indent=1, ensure_ascii=False) + "\n```" + prev}]
    if feedback:
        messages += [{"role": "assistant", "content": feedback[0]},
                     {"role": "user", "content": f"That output was rejected: {feedback[1]}. "
                      "Return the corrected complete HTML only."}]
    body = json.dumps({"model": MODEL, "messages": messages, "max_tokens": 6000, "temperature": 0.4}).encode()
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=body, headers={
        "Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json",
        "HTTP-Referer": "https://terminus.intern.dgmneto.com", "X-Title": "trmnl-ai"})
    with urllib.request.urlopen(req, timeout=180) as r:
        resp = json.load(r)
    u = resp.get("usage", {})
    log(f"llm {resp.get('model', MODEL)} in={u.get('prompt_tokens')} out={u.get('completion_tokens')} "
        f"cost=${u.get('cost', '?')}")
    return resp["choices"][0]["message"]["content"]


def extract_html(raw):
    m = re.search(r"```(?:html)?\s*\n(.*?)```", raw, re.S)
    html = (m.group(1) if m else raw).strip()
    if "<script" in html.lower():
        return None, "contains <script>"
    if re.search(r"""(src|href)\s*=\s*["']?\s*(https?:)?//""", html, re.I) or "url(http" in html:
        return None, "references an external URL"
    if len(html) > 40000:
        return None, f"too long ({len(html)} chars, max 40000)"
    if "view--full" not in html:
        return None, 'missing the root <div class="view view--full">'
    return html, None


def fallback_html(data):
    g = data["generated_for"]
    rows = ""
    for l in data.get("lines_now") or []:
        if isinstance(l, dict) and "line" in l:
            rows += (f'<div style="display:flex;justify-content:space-between;width:100%"><span class="title">{l["line"]}</span>'
                     f'<span class="title">{l["statuses"][0]["status"]}</span></div>')
    return (f'<div class="view view--full"><div class="layout layout--col gap--medium" style="padding:16px;align-items:stretch">'
            f'<span class="title">{g["target_label"]} · {g["now_local"]}</span>{rows}'
            f'<span class="label">AI screen unavailable — fallback</span></div></div>')


# ---------- state ----------

def path(name):
    return os.path.join(DATA_DIR, name)


def write_json(name, obj):
    tmp = path(name + ".tmp")
    with open(tmp, "w") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path(name))


def read_json(name):
    try:
        with open(path(name)) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def quiet_now():
    a, b = (int(x) for x in QUIET.split("-"))
    h = dt.datetime.now(TZ).hour
    return a <= h < b if a <= b else (h >= a or h < b)


def cycle(force=False, fixture=None, fresh=False):
    data = json.load(open(fixture)) if fixture else collect()
    write_json("last_data.json", data)
    h = data_hash(data)
    cur = read_json("screen.json")
    age = time.time() - cur["generated_ts"] if cur else 1e9
    if not force:
        if cur and quiet_now():
            return
        if cur and (age < MIN_GAP or (h == cur.get("data_hash") and age < MAX_AGE)):
            return
    if not API_KEY:
        log("OPENROUTER_API_KEY not set; writing fallback")
        if not cur:
            write_screen(fallback_html(data), h, "fallback")
        return
    feedback = None
    for attempt in (1, 2):
        try:
            previous = None if fresh or not cur or cur.get("model") == "fallback" else cur["html"]
            raw = llm(data, feedback, previous)
        except Exception as e:
            log("llm call failed:", f"{type(e).__name__}: {e}"[:300])
            break
        with open(path("last_raw.txt"), "w") as f:
            f.write(raw)
        html, err = extract_html(raw)
        if html:
            write_screen(html, h, MODEL)
            return
        log(f"attempt {attempt} rejected: {err}")
        feedback = (raw, err)
    if not cur:
        write_screen(fallback_html(data), h, "fallback")
    else:
        log("keeping previous screen from", cur["generated_at"])


def write_screen(html, h, model):
    now = dt.datetime.now(TZ)
    with lock:
        write_json("screen.json", {"html": html, "generated_at": now.strftime("%Y-%m-%d %H:%M"),
                                   "generated_ts": now.timestamp(), "model": model, "data_hash": h})
    log("screen written", model, len(html), "chars")


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        name = {"/screen.json": "screen.json", "/data.json": "last_data.json"}.get(self.path.split("?")[0])
        body = None
        if name:
            with lock:
                try:
                    body = open(path(name), "rb").read()
                except OSError:
                    pass
        if self.path.startswith("/preview") and body is None:
            s = read_json("screen.json")
            if s:
                body = ('<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" '
                        'href="https://trmnl.com/css/latest/plugins.css"></head><body class="trmnl">'
                        '<div class="screen screen--og_plus screen--2bit screen--landscape screen--md '
                        'screen--density-1x" style="--screen-w:800px;--screen-h:480px;width:800px;height:480px;'
                        f'outline:1px solid red">{s["html"]}</div></body></html>').encode()
        if body is None:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8" if self.path.startswith("/preview")
                         else "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--once", action="store_true")
    p.add_argument("--force", action="store_true")
    p.add_argument("--data", help="fixture JSON to use instead of live fetches")
    p.add_argument("--fresh", action="store_true", help="don't show the LLM the previous screen (after prompt changes)")
    a = p.parse_args()
    os.makedirs(DATA_DIR, exist_ok=True)
    if a.once:
        cycle(a.force, a.data, a.fresh)
        return
    srv = http.server.ThreadingHTTPServer(("0.0.0.0", 8080), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    log(f"serving :8080, model={MODEL}, fetch every {FETCH_EVERY}s")
    while True:
        try:
            cycle()
        except Exception as e:
            log("cycle error:", f"{type(e).__name__}: {e}")
        time.sleep(FETCH_EVERY)


if __name__ == "__main__":
    sys.exit(main())
