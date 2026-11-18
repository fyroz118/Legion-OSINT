# Legion-OSINT

Bangladesh-priority, global public-source OSINT reporting. The collection workflow gathers public Telegram preview posts plus public RSS/Atom headlines and excerpts. The on-demand Gemini workflow can organise collected evidence and draft the report. It does not require a Telegram account session, Telegram API credentials, a VPS or Tavily.

## Reporting model

- Bangladesh first, then South Asia, MENA and other regions represented in configured public channels.
- Ten-section daily report, individual source-post briefs, CSV evidence register and JSON coverage summary.
- Target 50+ source briefs when configured channels expose enough relevant posts; never pad counts or treat multiple posts as unique incidents. The configured Telegram registry now contains 85 public channels spanning Bangladesh, Myanmar, Ukraine, the Middle East, Europe, East/Southeast Asia, Sri Lanka, Ethiopia and Latin America. It deliberately mixes independent newsrooms, official/institutional feeds, political-party actor channels and unverified OSINT/commentary aggregators; source affiliation and perspective are disclosed, not treated as proof of reliability.
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
- `telegram_posts.csv` — Telegram evidence register.
- `news_articles.csv` — public RSS/Atom headlines and excerpts.
- `news_collection_summary.json` — publisher-level feed diagnostics.
- `collection_summary.json` — counts, page totals and channel errors.

## Expand the source network

The active registry is intentionally kept separate from unreviewed discoveries. Run the [automated discovery workflow](../../actions/workflows/discover-telegram-channels.yml) to build the cumulative candidate pool without manually collecting channel links. You may still contribute a TXT/CSV list through [CHANNEL_LIST_INTAKE.md](CHANNEL_LIST_INTAKE.md), but this is optional. Unreviewed candidates are never automatically treated as reliable or enabled. A 1,000+ candidate pool is a target, not a promise that 1,000 channels will be found, active or fetched in every run.

## Coverage limitations

The Telegram collector reads enabled usernames in [config/channels.json](config/channels.json) using public Telegram preview pages (`https://t.me/s/<channel>`). A separate RSS/Atom collector reads the public feeds listed in [config/news_sources.json](config/news_sources.json), collecting only headlines and short feed excerpts. It attempts bounded pagination up to the selected cap and stops when it reaches dates earlier than the reporting date.

**This mode does not authenticate to Telegram and cannot use Telegram global search.** It covers only the finite configured channel list and whatever history Telegram exposes through public previews. It does not directly search X, Facebook or YouTube. RSS/Atom coverage is limited to the explicitly configured feeds; it is not a general web crawler or a full-article scraper. Pagination, historical availability, media extraction and rate limits may vary. The collector records per-channel preview dates, date-matched counts and stop reasons to distinguish inactive/stale previews from parser failures. Configured source class, affiliation, language, region and editorial notes are carried into the evidence CSV and individual briefs. Gemini transient 429/5xx service failures receive bounded exponential-backoff retries before the evidence-preservation fallback is used. 50+ briefs cannot be guaranteed; missing posts do not mean no incidents occurred.

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

Use [Discover Telegram channel candidates](../../actions/workflows/discover-telegram-channels.yml) for a no-secret, no-login discovery pass. It searches 84 Bangladesh-first multilingual regional and political queries across public web indexes and crawls 31 configured public directory pages across Bangladesh, India, Myanmar, Pakistan, Sri Lanka, Nepal, Afghanistan, Ukraine, Palestine, Sudan, Ethiopia, MENA, Africa, Southeast Asia and the Americas. Supported directory link formats include TG Market channel profiles, TGScope country catalogues and Telemetrio channel profiles. It deduplicates usernames, checks up to 250 public previews, and uploads CSV/JSON registries plus provider and directory diagnostics as a 30-day artifact.

The workflow now runs **hourly at minute 17 UTC** (minute 17 each hour in Bangladesh time as well) and can also be started manually. It performs syntax and parser self-tests before network discovery. Provider errors, empty result pages and blocked/challenge pages are recorded separately. If every provider yields zero Telegram links and there is no existing registry, the run fails visibly rather than reporting an empty discovery as success.

**Important:** this is public web-index discovery, not Telegram's authenticated global channel search. Search indexes are incomplete and biased, and automated requests may be blocked. Candidates are labelled `UNREVIEWED_CANDIDATE`, source class/affiliation remain unknown or unassessed, and `enabled_for_collection=false`. No candidate is auto-promoted to `config/channels.json`. A 1,000+ candidate pool is a target, not a guarantee. Directory listings and social links are leads; verify identity, language, region, activity and editorial relationship before approval.


## Public news-feed collection

The scheduled collection workflow now runs two independent collectors: (1) configured public Telegram preview pages and (2) configured public RSS/Atom feeds. The RSS layer currently enables seven Bangladesh and Myanmar publisher feeds, including national and regional newsrooms. The bdnews24.com endpoint is retained as a disabled candidate because it currently returns HTML rather than parseable RSS. It retains publisher name, feed URL, article URL, publication time, language, region, source class and affiliation. It collects only public feed headlines/excerpts, not full article bodies. RSS items are included in the same read-only TBC feed as Telegram posts, with `platform` identifying the source type and every item marked `UNVERIFIED`. RSS source errors are reported per publisher and do not erase successful Telegram collection. The default RSS lookback is 72 hours to reduce gaps between scheduled runs; duplicate source IDs are removed when the TBC feed is built.

The discovery query set includes Bangladesh district/labour-rights and party-network terms (Awami League, BNP, Jamaat-e-Islami, student wings), Indian party/state-unit terms (BJP, Congress, AAP, CPI(M), DMK and regional movements), Myanmar state/region terms, South Asia, Palestine, Sudan, Sahel/DRC and Ukraine local-reporting terms. The seed pool currently contains 73 new unreviewed candidate handles (existing active allowlist channels are kept separate) across Bangladesh, India, Myanmar, Ukraine and Palestine. These are leads, not verified active channels. Candidate discovery remains separate from the active registry: no candidate is automatically enabled, and source identity/activity/independence must be reviewed before collection. The 31 directory URLs are discovery inputs, not a claim that each route exists or yields results; route failures are reported.


### Bangladesh Telegram directory seeds

The discovery pool now also imports a small set of Bangladesh public-directory leads from [TG Market's Bangladesh news category](https://tgmarket.io/countries/bd/news). These are stored in [discovery/seed_candidates.json](discovery/seed_candidates.json) and merged into the cumulative candidate registry. Directory category labels and subscriber counts are not source verification. The seeded channels remain `UNREVIEWED_CANDIDATE`, have unknown/unassessed source identity, and stay `enabled_for_collection=false`. Movement, party, advocacy and aggregator accounts must be classified as actor-originated or unknown where appropriate; none should be treated as independent corroboration without separate evidence.


### Official-source Telegram layer

The active registry includes official/institutional Telegram feeds as a parallel source layer, separate from independent newsrooms and unofficial/actor-originated sources. Five authenticated public channels were added in November 2026: India's Ministry of Information & Broadcasting (`@MIB_India`), the Russian Embassy in Bangladesh (`@rusembbd`), Iran's IRNA English service (`@Irna_en`), TASS English (`@tassagency_en`) Anadolu Agency English (`@anadoluagency_en`) Qatar News Agency (`@QatarNewsAgency`) and Emirates News Agency WAM (`@wamnews_en`). Official channels for Bangladesh BSS/BTV/Betar were not added because an authentic public Telegram channel was not established during this review. Official statements are attributed to their issuing institution and are not treated as independent confirmation.
