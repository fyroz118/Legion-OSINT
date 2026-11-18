# Legion-OSINT

A local-first, evidence-aware OSINT monitoring starter for curated accessible public Telegram sources, with a private Telegram command bot and Gemini-assisted Q&A.

## Scope
Bangladesh-first, global coverage; English primary with Bangla and other local languages supported as source data. Reporting timezone target: Asia/Dhaka.

## Safety and collection boundaries
- Collect only from a curated allowlist of accessible public channels.
- Respect Telegram terms, rate limits, access controls, and local law.
- No private-group scraping, access-control bypass, doxxing, private-person profiling, targeting, or assistance that facilitates violence.
- Treat social posts as leads, not verified facts. Repetition is not independent corroboration.
- Preserve source links, publication timestamps, collection timestamps, and uncertainty.
- Gemini summarizes retrieved records; it is not an autonomous fact-checker.

## Setup
1. Install Python 3.10+.
2. Install dependencies: `pip install -r requirements.txt`.
3. Copy `.env.example` to a local `.env` and fill credentials.
4. Add reviewed public channel usernames to `config/channels.json`.
5. Set your own numeric Telegram user ID in `TELEGRAM_ALLOWED_USER_IDS`.
6. Run `python -m app.collector` once, then `python -m app.bot`.

Get Telegram API credentials from https://my.telegram.org, a bot token from @BotFather, and a Gemini key from Google AI Studio. Never paste credentials into chat or commit `.env`, Telegram session files, or API keys.

## Commands
- `/status` — database count
- `/daily` — recent global posts
- `/bangladesh` — Bangladesh posts
- `/search <terms>` — text search
- `/ask <question>` — Gemini answer grounded in collected records
- `/help` — help

## Evidence standard
Use `VERIFIED` only when independent corroboration is documented; otherwise retain `CREDIBLE_LEAD`, `DISPUTED`, or `UNVERIFIED`. Use `MISLEADING_FALSE` only when evidence demonstrates it. Keep incident date distinct from post date. Do not infer imminent violence from rhetoric alone.

## Current limitations
This is a starter scaffold: one-shot collection, simple text search, no scheduler, no automated language identification, no validated incident extraction, no comprehensive Telegram coverage, and no analyst-grade verification. Start with 2–5 sources and validate carefully.

## Layout
```
app/       collector, database, Gemini helper, Telegram bot
config/    public channel allowlist and keyword lists
.env.example
requirements.txt
```

This is not a validated intelligence product and does not guarantee comprehensive Telegram coverage, accurate geolocation, or verified incident reporting.

## Beginner Android setup
See [ANDROID_SETUP.md](ANDROID_SETUP.md) for a step-by-step Pydroid 3 guide. The repository also includes `app/setup_check.py` and `run_preflight.py` for a local configuration check. The checker reports whether required settings are present but never prints their values.
