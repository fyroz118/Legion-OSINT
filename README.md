# Legion-OSINT

Bangladesh-priority, global public-source OSINT reporting. The on-demand workflow collects from **configured public Telegram channel preview pages** and uses **Gemini** to organise evidence and draft the report. It does not require a Telegram account session, Telegram API credentials, a VPS or Tavily.

## Reporting model

- Bangladesh first, then South Asia, MENA and other regions represented in configured public channels.
- Ten-section daily report, individual source-post briefs, CSV evidence register and JSON coverage summary.
- Target 50+ source briefs when configured channels expose enough relevant posts; never pad counts or treat multiple posts as unique incidents. The configured Telegram registry now contains 41 public channels spanning Bangladesh, Myanmar, Ukraine, the Middle East, Europe, East/Southeast Asia, Sri Lanka, Ethiopia and Latin America. It deliberately mixes independent newsrooms, official/institutional feeds, political-party actor channels and unverified OSINT/commentary aggregators; source affiliation and perspective are disclosed, not treated as proof of reliability.
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

## Expand the source network

The active registry is intentionally kept separate from unreviewed discoveries. Run the [automated discovery workflow](../../actions/workflows/discover-telegram-channels.yml) to build the cumulative candidate pool without manually collecting channel links. You may still contribute a TXT/CSV list through [CHANNEL_LIST_INTAKE.md](CHANNEL_LIST_INTAKE.md), but this is optional. Unreviewed candidates are never automatically treated as reliable or enabled. A 1,000+ candidate pool is a target, not a promise that 1,000 channels will be found, active or fetched in every run.

## Coverage limitations

The collector reads enabled usernames in [config/channels.json](config/channels.json) using public Telegram preview pages (`https://t.me/s/<channel>`). It attempts bounded pagination up to the selected cap and stops when it reaches dates earlier than the reporting date.

**This mode does not authenticate to Telegram and cannot use Telegram global search.** It covers only the finite configured channel list and whatever history Telegram exposes through public previews. It does not directly search X, Facebook, YouTube or general news websites. Pagination, historical availability, media extraction and rate limits may vary. The collector records per-channel preview dates, date-matched counts and stop reasons to distinguish inactive/stale previews from parser failures. Configured source class, affiliation, language, region and editorial notes are carried into the evidence CSV and individual briefs. Gemini transient 429/5xx service failures receive bounded exponential-backoff retries before the evidence-preservation fallback is used. 50+ briefs cannot be guaranteed; missing posts do not mean no incidents occurred.

## Verification and safety

- Gemini is not an independent fact-checker. Every post begins as an unverified claim.
- Publication time is not necessarily incident time; reposts are not independent corroboration.
- Do not infer motives, identities, casualties, locations or confidence from incomplete posts.
- Rhetoric alone does not establish imminent violence.
- Use only lawfully accessible public material; respect platform terms and rate limits.
- No private-group scraping, access-control bypass, doxxing, private-person profiling, targeting or tactical assistance facilitating violence.
- Disclose inaccessible channels and language/geographic gaps; never claim comprehensive coverage.

Other repository components include a separate Telegram bot and older authenticated collection/review modules; they are not used by this workflow. Actions artifacts are retained for 14 days. Never commit secrets, session strings or database files.


## Automated free Telegram channel discovery

Use [Discover Telegram channel candidates](../../actions/workflows/discover-telegram-channels.yml) for a no-secret, no-login discovery pass. It searches three public web indexes (DuckDuckGo, Bing and Google) using Bangladesh-first multilingual regional queries, extracts public `t.me` links, deduplicates usernames, checks up to 250 public previews, and uploads CSV/JSON registries plus provider diagnostics as a 30-day artifact.

The workflow runs daily at 08:15 Asia/Dhaka and can also be started manually. It performs syntax and parser self-tests before network discovery. Provider errors, empty result pages and blocked/challenge pages are recorded separately. If every provider yields zero Telegram links and there is no existing registry, the run fails visibly rather than reporting an empty discovery as success.

**Important:** this is public web-index discovery, not Telegram's authenticated global channel search. Search indexes are incomplete and biased, and automated requests may be blocked. Candidates are labelled `UNREVIEWED_CANDIDATE`, source class/affiliation remain unknown or unassessed, and `enabled_for_collection=false`. No candidate is auto-promoted to `config/channels.json`. A 1,000+ candidate pool is a target, not a guarantee. Directory listings and social links are leads; verify identity, language, region, activity and editorial relationship before approval.
