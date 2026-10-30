# Logbook — trmnl-ai

Reverse-chronological. Newest entry on top. One entry per task that touches **trmnl-ai** — what changed,
why, server commands run, verified outcome. See `../../LOGBOOK.md` for the project-wide log.

## 2026-10-30 — Live model → DeepSeek V4.1 Flash; "be bold" feedback
User picked DeepSeek V4.1 Flash. `.env` + `env.tpl` `OPENROUTER_MODEL=deepseek/deepseek-v4.1-flash`
(`.env` re-chmod 600 after `sed -i`), `app.py` now sends `reasoning:{enabled:false}` (env
`REASONING` override), max_tokens 8000; `docker compose up -d --force-recreate`. First user feedback
added to `prompt.md`: bold, ruthless about irrelevant info, no repeats. `--once --force --fresh` →
2054 out tokens, $0.0014; Terminus build of ext 2 viewed: big inverted temp + "✓ Clear" blocks, one
line per tube line, footer only for real disruptions (Central minor delays live). Preview updated.

## 2026-10-30 — Bake-off round 2: cheap / open-weight models
User asked for cheaper/open-source options. Re-ran with reasoning disabled (+ raw replies saved,
finish_reason recorded): 11 models, all produced HTML. Passed: DeepSeek V4 Flash ($0.0006),
DeepSeek V4.1 Flash ($0.0010), Gemma 4 31B ($0.0011), Haiku 5.5 reasoning-off ($0.0014), GLM 5.3
Flash (minor clip). Found Haiku had been reasoning in production (off = ~40% cheaper). MiniMax/GLM
reject `enabled:false` (400) → `effort:low`. All renders sent to user; table in README. Deleted the
`bakeoff_*` Terminus screens afterwards. Spend ≈ $0.02.

## 2026-10-30 — Model bake-off (10 OpenRouter models)
Ran the same data snapshot through 10 cheap/mid models, rendered 6 valid outputs via Terminus as
throwaway `bakeoff_*` screens (not on a playlist). Finalists for the user: Haiku 5.5 ($0.002),
Gemini 3.8 Flash ($0.017), Sonnet 5.5 ($0.049). Results table in README; scripts in `src/bakeoff/`.
Total spend ≈ $0.12.

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
Device 7 confirmed on it: NPM log 12:24:06 `/api/display` then `/uploads/7948dfe2….png` = screen 6's image.

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
