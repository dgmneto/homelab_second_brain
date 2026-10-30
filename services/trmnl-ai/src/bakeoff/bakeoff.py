"""Model bake-off: same data snapshot -> each model -> /data/bakeoff/<slug>.html + results.json.
Copy into the container and run (see ../../README.md "Choosing a model"):
  docker exec trmnl-ai cp /data/last_data.json /data/bakeoff/fixture.json
  docker exec trmnl-ai python /data/bakeoff/bakeoff.py <model> <model> ...
"""
import json, os, sys, time, threading, re
sys.path.insert(0, "/app")
import app
SUFFIX = os.environ.get("SUFFIX", "")  # e.g. "_r2" to keep earlier rounds
models = sys.argv[1:]
out = "/data/bakeoff"; os.makedirs(out, exist_ok=True)
data = json.load(open("/data/bakeoff/fixture.json"))
res = {}
def one(m):
    import urllib.request
    t = time.time()
    msgs = [{"role": "system", "content": open(app.PROMPT_FILE).read()},
            {"role": "user", "content": "Design the screen for this data:\n```json\n" + json.dumps(data, indent=1, ensure_ascii=False) + "\n```"}]
    body = json.dumps({"model": m, "messages": msgs, "max_tokens": int(os.environ.get("MAX_TOKENS", "12000")), "temperature": 0.4, "usage": {"include": True},
                       "reasoning": json.loads(os.environ.get("REASONING", '{"enabled": false}'))}).encode()
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=body, headers={
        "Authorization": f"Bearer {app.API_KEY}", "Content-Type": "application/json", "X-Title": "trmnl-ai bakeoff"})
    try:
        r = json.load(urllib.request.urlopen(req, timeout=300))
        ch = r["choices"][0]
        raw = ch["message"].get("content") or ""
        html, err = app.extract_html(raw)
        u = r.get("usage", {})
        slug = re.sub(r"[^a-z0-9]+", "_", m.lower()) + SUFFIX
        open(f"{out}/{slug}.raw.txt", "w").write(raw)
        if html: open(f"{out}/{slug}.html", "w").write(html)
        res[m] = {"slug": slug, "ok": bool(html), "err": err, "finish": ch.get("finish_reason"),
                  "reasoning_tokens": (u.get("completion_tokens_details") or {}).get("reasoning_tokens"), "in": u.get("prompt_tokens"), "out": u.get("completion_tokens"),
                  "cost": u.get("cost"), "secs": round(time.time() - t, 1)}
    except Exception as e:
        res[m] = {"ok": False, "err": f"{type(e).__name__}: {e}"[:200], "secs": round(time.time() - t, 1)}
ts = [threading.Thread(target=one, args=(m,)) for m in models]
[t.start() for t in ts]; [t.join() for t in ts]
json.dump(res, open(f"{out}/results{SUFFIX}.json", "w"), indent=1)
for m, r in res.items(): print(m, r)
