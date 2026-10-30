# Logbook — trmnl-ai

Reverse-chronological. Newest entry on top. One entry per task that touches **trmnl-ai** — what changed,
why, server commands run, verified outcome. See `../../LOGBOOK.md` for the project-wide log.

## 2026-10-30 — OpenRouter key in, first AI screens, prompt tuning, on device 7
User supplied a new OpenRouter key; written to the server `.env` only (600, ACLs stripped with
`setfacl -b` — the dir's default ACL had made it 664), container recreated. Iterated 4 renders,
viewing each Terminus PNG: (1) good design but gray small text dithered to broken glyphs → black-only
text, ≥16 px, weight ≥600 under 24 px; (2) overflowed right + bottom → fixed 800×480 root tag,
772×456 usable, explicit per-section pixel heights; (3) prompt edits weren't reaching the container
(`in=` tokens unchanged): single-file bind mounts pinned the old inode → compose now mounts the whole
dir; (4) fits, crisp. Added: previous screen HTML sent for layout stability, `--fresh` flag.
Haiku 5.5 cost ~$0.002–0.003/call. Swapped device 7 playlist item 5 → screen 6 (AI Board) via SQL.
Verified Terminus' own schedule rebuilt screen 6 (12:12) without a manual build.

## 2026-10-30 — Created trmnl-ai (LLM-designed TRMNL screen)
User asked for an AI-generated TRMNL screen (full HTML by the LLM, OpenRouter, replaces Morning Board,
weather + 3 lines + station disruptions + planned works; feedback goes into the prompt). Wrote
`app.py` (stdlib), `prompt.md`, `compose.yaml`, `env.tpl` (mirrored in `src/`); deployed to
`/home/dgmneto/homelab/services/trmnl-ai/` as dgmneto, data dir `/footage/services/trmnl-ai/data`
(chown 1000), added per-service `.gitignore` for `.env` (the server repo's root .gitignore does NOT
cover `.env`). `docker compose up -d` → container up on internalNetwork 172.21.0.141. Verified a
live fetch (all 7 sources OK, ~3 KB trimmed JSON; Piccadilly part closure showed up) and that
terminus fetches `http://trmnl-ai:8080/screen.json` (200). No OpenRouter key yet → serving the
deterministic fallback. Fixed fallback/prompt after the first PNG showed rows collapsing to content
width (`width:100%` needed). Model default `anthropic/claude-haiku-5.5`.
