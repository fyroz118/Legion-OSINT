# Legion-OSINT

Bangladesh-priority, global public-source OSINT reporting. The current on-demand workflow uses **Telegram (Telethon) for collection and Gemini for analysis**. It does not use Tavily or general web search.

## Reporting model

- Bangladesh first, then South Asia, MENA and other regions represented in the configured Telegram sources.
- Ten-section daily report, individual source-post briefs, CSV evidence register and JSON coverage summary.
- Target 50+ source briefs when the configured channels produce enough relevant posts; never pad counts or treat multiple posts as unique incidents.
- Greater attention to unofficial/local reporting, eyewitnesses and independent monitors, while retaining official/institutional channels as a parallel source layer.
- Rumours and allegations must remain clearly labelled UNVERIFIED RUMOUR.
- Reporting timezone: Asia/Dhaka (UTC+6).

See [MASTER_PROMPT.md](MASTER_PROMPT.md) for the full analytic specification.

## On-demand workflow (no VPS)

GitHub Actions starts a temporary runner only when manually triggered. It collects messages from configured accessible public Telegram channels and asks Gemini to structure the evidence into a report.

### One-time setup

1. Obtain Telegram API ID and API hash through Telegram's official developer portal.
2. Install Python 3.11 and dependencies in a trusted local environment: `pip install -r requirements.txt`.
3. Run `python scripts/export_telegram_session.py` and complete Telegram login locally. The script prints a Telethon StringSession.
4. Treat that session string as a password. Never send it in chat, commit it, or save it in a public file. Revoke it in Telegram if exposed.
5. In GitHub repository **Settings → Secrets and variables → Actions**, create these repository secrets:
   - `TELEGRAM_API_ID`
   - `TELEGRAM_API_HASH`
   - `TELETHON_SESSION_STRING`
   - `GEMINI_API_KEY`

### Run each report

1. Open **Actions → Run Legion-OSINT on demand → Run workflow**.
2. Enter the reporting date as `YYYY-MM-DD` in Asia/Dhaka.
3. Choose 100, 300 or 500 recent messages to inspect per configured channel.
4. Run the workflow and download the artifact `legion-osint-telegram-gemini-YYYY-MM-DD`.

### Output files

- `daily_intelligence_report.md` — Gemini-assisted ten-section report.
- `individual_source_briefs.md` — one brief per collected post.
- `telegram_posts.csv` — sortable evidence register.
- `collection_summary.json` — collection totals and channel errors.

## Sources and coverage

The collector reads only enabled channels in [config/channels.json](config/channels.json) that the authorised Telegram account can access. The list is a curated source set, not universal Telegram coverage. It inspects only the most recent configured number of messages per channel and keeps posts published on the requested Dhaka date. Expand the channel list only with reviewed, lawfully accessible public sources.

The current workflow does not search X, Facebook, YouTube, news websites or all public Telegram channels. It cannot guarantee that 50 posts will be available on every date. A source post is not a unique incident.

## Verification and safety

- Gemini summarises and organises supplied evidence; it is not an independent fact-checker.
- Every post begins as an unverified claim. Seek independent corroboration before presenting an incident as established.
- Publication time is not necessarily incident time.
- Reposts and syndicated copies are not independent corroboration.
- Do not infer motives, identities, casualties, locations or confidence from incomplete posts.
- Rhetoric alone does not establish imminent violence.
- Use only lawfully accessible public material; respect Telegram terms, rate limits and access controls.
- No private-group scraping, access-control bypass, doxxing, private-person profiling, targeting or tactical assistance facilitating violence.
- Disclose inaccessible channels and language/geographic gaps. Do not claim comprehensive coverage.

## Optional private Telegram bot

The repository also contains a separate Telegram command bot and analyst-review modules. They are not started by the on-demand workflow and are not required for generating reports. The current workflow does not preserve analyst review state between runs. GitHub Actions artifacts are retained for 14 days.

## Local validation

```bash
python scripts/validate_project.py
python -m py_compile scripts/*.py
python -m unittest discover -s tests -v
```

Never commit `.env`, API keys, Telegram session strings, session files or database files.
