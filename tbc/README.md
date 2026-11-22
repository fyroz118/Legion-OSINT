# Telebot Creator deployment notes

This is an import-ready TPY command package reconstructed from the current Legion-OSINT GitHub source. It does not include a Telegram token, GitHub token, Gemini key, private user ID, or analyst-history database.

## Files

- `legion_osint_tbc_import.json` — 25 commands in TBC's structured JSON command-import format.
- `legion_osint_tbc_import.txt` — same commands in TBC's documented plain-text import format.
- `../scripts/publish_tbc_feed.py` — builds a bounded read-only snapshot from public Telegram preview collection output.
- `../docs/feed/latest.json` — generated snapshot location; it appears after the first successful scheduled collection and publisher run.

## First-time TBC setup

1. In TBC, open the existing `@legion_osint_bot` and use **Manage → Import Commands**. Import `legion_osint_tbc_import.json` (or `legion_osint_tbc_import.txt` if you prefer the plain-text format). Do not choose the option to remove old commands; merge/update only.
2. Open the special `.env` command and set `OWNER_IDS` to a list containing your own numeric Telegram user ID. Initially it is empty by design:
   ```python
   OWNER_IDS = [123456789]
   FEED_URL = "https://raw.githubusercontent.com/fyroz118/Legion-OSINT/main/docs/feed/latest.json"
   ```
   Replace the example number with the value returned by `/myid`. Save the `.env` command.
3. Use `/start`, `/status`, `/daily`, and `/bangladesh` in a private chat to smoke-test the interface.
4. Use `/alerts_on` only after `/status` shows a current feed snapshot. Alerts check the published feed every two hours and start with existing posts marked as seen.
5. Keep the bot in **Working** state for scheduled alerts.

## Commands included

`/myid`, `/start`, `/help`, `/status`, `/daily`, `/bangladesh`, `/search`, `/leads`, `/briefs`, `/coverage`, `/report`, `/digest`, `/reviewqueue`, `/reviewlead`, `/candidates`, `/incidentdraft`, `/incidentqueue`, `/approveincident`, `/linklead`, `/ask`, `/research`, `/alerts_on`, `/alerts_off`, and internal scheduled command `alert_poll`.

## Current boundaries

- The public feed contains only public Telegram preview posts and collection diagnostics. It excludes analyst notes, incident drafts, credentials and user identifiers.
- The repository is public. The feed is therefore public too; do not place private records in it.
- Analyst review and incident workflow data are stored in TBC bot storage, not synchronized back to the existing SQLite database. Export/backup for that TBC storage must be validated separately.
- `/ask` and `/research` explicitly report that their external engines are not yet connected; they do not invent results.
- `/report` lists only analyst-approved incident records; approval is not verification. `/digest` is a separate unverified public-source digest. The full former ten-section report engine is not yet connected to TBC.
- The configured Telegram source list remains finite. The 1,000+ channel target is not achieved or claimed.
- Collection is still public preview-only. It is not Telegram global search and does not access private groups.

## Rollback safety

Do not dispatch `.github/workflows/personal-telegram-bot.yml` while TBC is active. That worker calls Telegram `deleteWebhook` before `getUpdates` polling, which conflicts with TBC's webhook delivery. Collection and discovery workflows are independent and remain active.


## RSS-aware TBC command update

The public feed now combines Telegram preview posts with RSS/Atom headlines and excerpts. The standard import package includes the updated `/news`, `/status`, `/coverage`, `/daily`, `/search`, `/bangladesh`, `/leads`, `/briefs`, `/reviewqueue` and `/digest` commands. For an existing TBC installation, use [legion_osint_tbc_news_update.json](legion_osint_tbc_news_update.json) or [legion_osint_tbc_news_update.txt](legion_osint_tbc_news_update.txt) to update only these commands without importing or overwriting the `.env` command. After import, rename the new `news` command to `/news` if TBC displays it without a leading slash. The update package does not contain owner IDs or credentials; preserve the existing `.env` configuration.


## Search behaviour

The `/search` command searches only the latest published collection snapshot. It matches every supplied word (AND matching) across post text, channel/publisher name, platform, source classification, affiliation, region and language. Example: `/search Bangladesh protest`. Results are limited to eight records per reply and remain unverified source leads. This is not Telegram global search and cannot retrieve posts absent from the collection snapshot.


## Date-based news retrieval

Import the updated command package to add `/date YYYY-MM-DD`. The collection workflow maintains a daily archive at `docs/feed/archive/YYYY-MM-DD.json`, merging each scheduled run so earlier posts from the same day are retained. The bot fetches that date-specific archive and returns Telegram plus RSS/Atom source records in chronological order, using the feed timezone (normally Asia/Dhaka). Each request returns a page of up to 20 records; use the next-page command shown by the bot to browse the entire day's archive. Archives begin only after this feature is deployed; older dates cannot be reconstructed automatically. Collection remains bounded by public Telegram previews, RSS/Atom access and configured collector limits. Results are unverified source leads, not verified incidents.

## Fully automatic public Telegram channel discovery

- `scripts/discover_public_telegram.py` searches public search-index RSS results for Telegram channel links and inspects unauthenticated public previews.
- `.github/workflows/autonomous-channel-discovery.yml` runs every six hours and can be manually dispatched.
- **Every newly discovered channel with an accessible public Telegram preview is automatically added to `config/channels.json` and enabled for collection.** Political-party, activist, community, newsroom, specialist and unknown channels are all included; classification is descriptive and does not endorse a source.
- New sources retain an explicit source class, discovery URL, timestamp and notes. Posts remain UNVERIFIED. An accessible preview does not establish identity, reliability or editorial independence.
- Unavailable, invalid or non-channel URLs are not activated. Existing candidates are not bulk-promoted merely by changing the policy; they remain in the legacy candidate registry.
- TBC `/discover` and `/discovery_status` display the latest run and activation counts. `/candidates` is now a legacy/exception queue; manual approve/reject commands remain optional overrides, not required steps in the normal discovery pipeline.
- The search method uses public search-index RSS and public Telegram previews. It is not Telegram global search, has incomplete coverage and does not access private groups.

Import the updated `tbc/legion_osint_tbc_news_update.json` or `.txt` package through Manage → Import Commands (merge/update). No GitHub write token is needed for automatic discovery or activation because GitHub Actions writes the registry directly. The TBC token is only needed for optional manual approve/reject overrides.


## V11 expanded analyst-review summary command

The repository includes `summary_v11_command.txt` for the owner-only private-chat `/summary` command. V11 displays multi-label claim types so physical-event claims are not hidden by preparation language, shows provisional source-lead IDs, reports the Bangladesh excluded-post audit sample, and labels partial-day comparisons. Category totals may overlap. Provisional IDs identify source posts, not unique incidents. It contains no `while` loop.

GitHub publication does not deploy commands into Telebot Creator. For an existing installation, manually replace only the existing `/summary` command with the contents of `summary_v11_command.txt`. Preserve the existing `.env`, OWNER_IDS, FEED_URL and webhook configuration. Do not import the recovery package and do not run the personal Telegram bot workflow. V12 collector/report changes have regression tests, but a successful GitHub Actions run and live TBC runtime test have not been confirmed. Do not claim V12 is fully validated or deployed until those checks pass.


## V12 final analyst-review command and publisher

See [the V12 methodology and validation notes](INTELLIGENCE_REPORT_V12.md).

V12 adds Bengali-language Bangladesh phrase triggers, commentary-context suppression for completed-incident classification, explicit overlap/source-record counts, and all configured monitoring regions including zero-relevance regions. Phrase matches remain unverified review leads; no motive, perpetrator, event location, unique incident or risk rating is inferred.

For the existing TBC bot, replace only `/summary` with `summary_v12_command.txt` after a V12 archive is published. The command refuses older archive versions. GitHub commits do not deploy into Telebot Creator. Preserve `.env`, OWNER_IDS, FEED_URL, webhook settings and alerts. Do not import the recovery package or run the personal Telegram bot workflow. A live TBC smoke test remains manual; no deployment is claimed.


## Muslim-targeted Hatewatch v2

Hatewatch v2 replaces the narrow exact-phrase starter classifier with a recall-oriented multilingual review classifier. It uses separate target, action, discrimination, propaganda and communal-tension indicators across English, Bengali, Hindi and Urdu. Target and action terms may appear in either order. It adds coverage for mob attacks, lynching, torture, killings, arson, mosque vandalism, demolition/eviction, detention, exclusion and policy-related discrimination, plus propaganda narratives including the reported "Bhagwa love trap" phrase. A phrase match remains an UNVERIFIED source lead; it does not establish that an allegation is true, that an event was religiously motivated, or that an individual committed wrongdoing. Historical, fact-checking and condemnation contexts are exposed for analyst review rather than silently discarded.

The RSS registry adds ten Google News discovery feeds focused on India (English/Hindi), Bangladesh (Bengali), Pakistan (English/Urdu), Afghanistan, Sri Lanka, Nepal, Myanmar/Rohingya and global Islamophobia. These are discovery aggregators, not primary sources. Each result must be traced to its underlying publisher; the publisher's identity, evidence and independence must be assessed. RSS collection is limited to public feed results in the collector's 72-hour window and source/item caps. Public Telegram preview collection remains bounded by the configured channel list. This is not comprehensive global monitoring and does not search private groups or social platforms globally.

The publisher emits `hatewatch_version: 2`, source-post screening counts, overlapping category counts and source links. The existing TBC `/hatewatch` command has been updated to require v2 and display the new match structure. GitHub publication does not deploy code into Telebot Creator: manually replace only the existing `/hatewatch` command with [hatewatch_tbc_command.txt](hatewatch_tbc_command.txt). Preserve `.env`, OWNER_IDS, FEED_URL, webhook settings, alerts and `/summary`. After a successful collection/publisher run, run `/hatewatch` again.

A zero-match result means only that configured feeds and rules returned no leads in that bounded window; it must never be interpreted as zero incidents. The system does not independently establish event location, event date, religious identity, motive, perpetrator, legal classification or corroboration. Analysts must review original linked sources and seek independent reporting, human-rights documentation, official responses and primary evidence.

## Ten-section daily intelligence report formatter

The former `/summary` command displayed the collector's internal 11-part triage schema rather than the requested ten-section intelligence-report layout. The replacement display command is `summary_v13_command.txt`. It reformats the existing V12 archive into the requested ten headings: executive summary, Bangladesh, international conflict/security, communal/social violence (including Hatewatch when present), political developments, information environment, incident register, early-warning assessment, source/coverage assessment, and overall judgment.

This is a **report-layout and evidence-labeling fix**, not a new research engine. It only uses records already present in the daily archive. It does not independently search X, Facebook or YouTube; it does not perform full fact-checking, geolocation, event-level deduplication, independent corroboration, or risk forecasting. It explicitly marks unsupported sections as not assessed rather than inventing findings. Source timestamps remain as stored and are not guaranteed to be converted to Bangladesh Standard Time.

For the existing TBC bot, replace only the existing `/summary` command with the complete contents of `summary_v13_command.txt`. Keep the command name `summary`. No `.env`, owner IDs, webhook, alert settings, collector or `/hatewatch` changes are required. GitHub publication does not deploy the command into TBC; a manual paste/save and TBC runtime test are still required.
