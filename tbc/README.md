# Telebot Creator deployment notes

This is an import-ready TPY command package reconstructed from the current Legion-OSINT GitHub source. It does not include a Telegram token, GitHub token, Gemini key, private user ID, or analyst-history database.

## Files

- `legion_osint_tbc_import.json` — 25 commands in TBC's structured JSON command-import format.
- `legion_osint_tbc_import.txt` — same commands in TBC's documented plain-text import format.
- `../scripts/publish_tbc_feed.py` — builds a bounded read-only snapshot from public Telegram preview collection output.
- `../docs/feed/latest.json` — generated snapshot location; it appears after the first successful scheduled collection and publisher run.

## First-time TBC setup

1. In TBC, open the existing `@legion_osint_bot` and use **Manage → Import Commands**. Import `legion_osint_tbc_import.json`. Do not choose the option to remove old commands; merge/update only.
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
