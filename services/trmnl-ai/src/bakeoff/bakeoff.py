"""Model bake-off: same data snapshot -> each model -> /data/bakeoff/<slug>.html + results.json.
Copy into the container and run (see ../../README.md "Choosing a model"):
  docker exec trmnl-ai cp /data/last_data.json /data/bakeoff/fixture.json
  docker exec trmnl-ai python /data/bakeoff/bakeoff.py <model> <model> ...
"""
import json, os, sys, time, threading, re
sys.path.insert(0, "/app")
import app
models = sys.argv[1:]
out = "/data/bakeoff"; os.makedirs(out, exist_ok=True)
data = json.load(open("/data/bakeoff/fixture.json"))
res = {}
def one(m):
    import urllib.request
    t = time.time()
    msgs = [{"role": "system", "content": open(app.PROMPT_FILE).read()},
            {"role": "user", "content": "Design the screen for this data:\n```json\n" + json.dumps(data, indent=1, ensure_ascii=False) + "\n```"}]
    body = json.dumps({"model": m, "messages": msgs, "max_tokens": 8000, "temperature": 0.4, "usage": {"include": True}}).encode()
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=body, headers={
        "Authorization": f"Bearer {app.API_KEY}", "Content-Type": "application/json", "X-Title": "trmnl-ai bakeoff"})
    try:
        r = json.load(urllib.request.urlopen(req, timeout=300))
        raw = r["choices"][0]["message"]["content"] or ""
        html, err = app.extract_html(raw)
        u = r.get("usage", {})
        slug = re.sub(r"[^a-z0-9]+", "_", m.lower())
        if html: open(f"{out}/{slug}.html", "w").write(html)
        res[m] = {"slug": slug, "ok": bool(html), "err": err, "in": u.get("prompt_tokens"), "out": u.get("completion_tokens"),
                  "cost": u.get("cost"), "secs": round(time.time() - t, 1)}
    except Exception as e:
        res[m] = {"ok": False, "err": f"{type(e).__name__}: {e}"[:200], "secs": round(time.time() - t, 1)}
ts = [threading.Thread(target=one, args=(m,)) for m in models]
[t.start() for t in ts]; [t.join() for t in ts]
json.dump(res, open(f"{out}/results.json", "w"), indent=1)
for m, r in res.items(): print(m, r)
