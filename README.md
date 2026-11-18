# Legion-OSINT

Bangladesh-priority, global public-source OSINT reporting. The on-demand workflow collects from **configured public Telegram channel preview pages** and uses **Gemini** to organise evidence and draft the report. It does not require a Telegram account session, Telegram API credentials, a VPS or Tavily.

## Reporting model

- Bangladesh first, then South Asia, MENA and other regions represented in configured public channels.
- Ten-section daily report, individual source-post briefs, CSV evidence register and JSON coverage summary.
- Target 50+ source briefs when configured channels expose enough relevant posts; never pad counts or treat multiple posts as unique incidents.
- Independent/local reporting receives attention, with official/institutional channels retained as a parallel source layer.
- Rumours and allegations remain clearly labelled UNVERIFIED RUMOUR.
- Reporting timezone: Asia/Dhaka (UTC+6).

See [MASTER_PROMPT.md](MASTER_PROMPT.md) for the analytic specification.

## One-time setup

1. Create a Gemini API key at [Google AI Studio](https://aistudio.google.com/app/apikey).
2. In this repository, open **Settings → Secrets and variables → Actions**.
3. Add one repository secret named `GEMINI_API_KEY`. Never paste the key into chat, workflow inputs, source files or commits.

No Telegram developer portal, Telegram login, API ID/hash, session string, local Python setup or VPS is required.

## Run a report

1. Open [Actions](../../actions).
2. Select **Run Legion-OSINT on demand** → **Run workflow**.
3. Enter the reporting date as `YYYY-MM-DD` in Asia/Dhaka.
4. Choose 100, 300 or 500 messages as the per-channel inspection cap.
5. Start the workflow and download `legion-osint-public-telegram-gemini-YYYY-MM-DD`.

## Outputs

- `daily_intelligence_report.md` — Gemini-assisted ten-section report.
- `individual_source_briefs.md` — one brief per collected post.
- `telegram_posts.csv` — evidence register.
- `collection_summary.json` — counts, page totals and channel errors.

## Coverage limitations

The collector reads enabled usernames in [config/channels.json](config/channels.json) using public Telegram preview pages (`https://t.me/s/<channel>`). It attempts bounded pagination up to the selected cap and stops when it reaches dates earlier than the reporting date.

**This mode does not authenticate to Telegram and cannot use Telegram global search.** It covers only the finite configured channel list and whatever history Telegram exposes through public previews. It does not directly search X, Facebook, YouTube or general news websites. Pagination, historical availability, media extraction and rate limits may vary. 50+ briefs cannot be guaranteed; missing posts do not mean no incidents occurred.

## Verification and safety

- Gemini is not an independent fact-checker. Every post begins as an unverified claim.
- Publication time is not necessarily incident time; reposts are not independent corroboration.
- Do not infer motives, identities, casualties, locations or confidence from incomplete posts.
- Rhetoric alone does not establish imminent violence.
- Use only lawfully accessible public material; respect platform terms and rate limits.
- No private-group scraping, access-control bypass, doxxing, private-person profiling, targeting or tactical assistance facilitating violence.
- Disclose inaccessible channels and language/geographic gaps; never claim comprehensive coverage.

Other repository components include a separate Telegram bot and older authenticated collection/review modules; they are not used by this workflow. Actions artifacts are retained for 14 days. Never commit secrets, session strings or database files.
