# Legion-OSINT cloud deployment

The recommended production shape is a persistent Linux host running two Docker services:
- `bot`: private Telegram Bot API interface.
- `collector`: scheduled Telethon collection worker.

Both services share a persistent Docker volume for the SQLite database and Telethon session. Do not use ephemeral storage: the session and database must persist across restarts.

## Required deployment secrets

Set these as environment variables in the hosting provider's private service settings. Do not commit a `.env` file.

- `TELEGRAM_API_ID`
- `TELEGRAM_API_HASH`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_ALLOWED_USER_IDS` (your own numeric Telegram user ID)
- `GEMINI_API_KEY`
- `GEMINI_MODEL=gemini-2.5-flash`
- `TAVILY_API_KEY` (required only for `/research`; keep it private)
- `TAVILY_SEARCH_DEPTH=basic`
- `RESEARCH_MAX_QUERIES=12`
- `DATABASE_PATH=/app/data/legion_osint.sqlite3`
- `TELETHON_SESSION_PATH=/app/data/legion_osint_user`
- `COLLECT_INTERVAL_MINUTES=60`
- `COLLECT_LIMIT_PER_CHANNEL=100`
- `REPORT_TIMEZONE=Asia/Dhaka`

## First-time Telethon authorization

Telethon user sessions require a one-time interactive login using the account's phone number and Telegram login code (and 2FA password if enabled). This authorization cannot be completed by a bot token alone.

On a trusted host with a terminal, run the collector once interactively before starting the persistent services:

```bash
docker compose run --rm collector python -m app.collector
```

Enter the Telegram phone number and login code in the terminal prompt. Never send the code or session file to anyone. The session is stored in the persistent `legion_data` volume. Once login completes, start the services:

```bash
docker compose up -d --build
```

If the hosting provider does not provide a secure interactive terminal, do not attempt to send login codes through chat or logs. Use a trusted one-time terminal environment to create the session, then transfer it securely to the persistent host.

## Source configuration

Before starting the collector, replace the placeholder in `config/channels.json` with a short, reviewed allowlist of accessible public channels. Begin with 2–5 sources. Respect platform rules and access controls; do not collect private groups or bypass restrictions.

## Operational checks

- Bot: send `/start` and `/status` from the authorized private Telegram account.
- Collector: inspect host logs for successful collection and rate-limit messages.
- Database: verify new records are stored and de-duplicated.
- Gemini: use `/ask` only after records have been collected.
- Public-web research: set `TAVILY_API_KEY`, then test `/research YYYY-MM-DD`, `/leads YYYY-MM-DD` and `/coverage YYYY-MM-DD`. This uses date-scoped news search and does not provide direct access to every social platform.
- Back up the persistent volume securely.

## Important limits

This is a self-hosted starter, not a validated intelligence product. Collection coverage depends on the reviewed channel allowlist and Telegram access. Gemini can summarize records but cannot independently verify them. Do not infer imminent violence from rhetoric alone. Keep reports aggregate and avoid private-person profiling, doxxing, or sensitive operational details.
