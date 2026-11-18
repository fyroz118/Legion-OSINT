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

## Autonomous public Telegram channel discovery (hybrid)

The repository now includes a scheduled discovery backend:
- `scripts/discover_public_telegram.py` searches public search-index RSS results for public Telegram channel links, then inspects unauthenticated `t.me/s/<username>` previews.
- `.github/workflows/autonomous-channel-discovery.yml` runs every 6 hours and can also be started manually from GitHub Actions.
- New channels are deduplicated against both active and candidate registries.
- Conservative automatic activation is limited to channels whose public preview shows a verification marker, newsroom-like identity signals, and at least one external link. These are screening signals, not proof of independence; activated sources remain subject to monitoring and all posts remain UNVERIFIED.
- Political-party, activist, community, unknown-operator and uncertain sources stay in the candidate queue for owner review.
- This is not Telegram global search. It uses public search-index results and public previews only; coverage is incomplete and search engines may return no Telegram results.

### New TBC commands

Import the updated `tbc/legion_osint_tbc_news_update.json` or `.txt` package using Manage → Import Commands (merge/update). New commands:
- `/discover` — latest discovery run and new channels.
- `/discovery_status` — discovery counts, timestamp and errors.
- `/candidates` — pending review queue.
- `/addchannel USERNAME` — owner approval of a candidate already in the queue.
- `/rejectchannel USERNAME` — owner rejection; keeps an audit record.

### TBC GitHub decision token

The two decision commands submit GitHub `repository_dispatch` events. Configure a dedicated GitHub fine-grained token in TBC's environment as `GITHUB_TOKEN`, restricted to this public repository with **Contents: read and write** permission. Do not put the token in command source, chat messages, or GitHub files. If TBC does not expose environment variables or its HTTP client does not support `HTTP.post(..., headers=..., json=...)`, the read-only discovery commands still work, but approvals must be made through the repository until the TBC runtime integration is adjusted.

Approval workflow: `.github/workflows/channel-discovery-decisions.yml`. It only approves usernames already present in `discovery/seed_candidates.json`; it cannot add arbitrary channel names. Approval enables collection but does not verify source identity or event claims.

The discovery report is published at `docs` path `discovery/latest.json` and the candidate queue remains in `discovery/seed_candidates.json`. Scheduled collection is triggered by the resulting change to `config/channels.json`.
