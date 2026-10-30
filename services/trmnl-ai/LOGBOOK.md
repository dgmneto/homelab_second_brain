# Logbook — trmnl-ai

Reverse-chronological. Newest entry on top. One entry per task that touches **trmnl-ai** — what changed,
why, server commands run, verified outcome. See `../../LOGBOOK.md` for the project-wide log.

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
