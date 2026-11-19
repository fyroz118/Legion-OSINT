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


## V8 expanded summary command

The repository includes `summary_v8_command.txt` for the owner-only private-chat `/summary` command. It prints reconciled Bangladesh counts, record types, exact-text candidate groups and date-labelled temporal comparison rows. It contains no `while` loop and is designed for manual replacement of the existing `/summary` command. GitHub publication does not deploy this command to TBC; preserve the existing `.env` and webhook configuration.
