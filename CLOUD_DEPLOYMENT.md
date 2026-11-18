# Legion-OSINT deployment

## Recommended: on-demand public Telegram + Gemini workflow (no VPS)

The manual GitHub Actions workflow starts a temporary runner only when triggered. It reads configured public Telegram channel preview pages and uses Gemini for synthesis. No persistent host or Telegram account session is required.

### One-time setup

1. Create a Gemini API key at https://aistudio.google.com/app/apikey.
2. In the GitHub repository, open **Settings → Secrets and variables → Actions**.
3. Add a repository secret named `GEMINI_API_KEY`. Never put the key in chat, workflow inputs or committed files.

No Telegram developer portal, API ID/hash, Telethon StringSession, local terminal setup or VPS is required.

### Run a report

1. Open **Actions → Run Legion-OSINT on demand → Run workflow**.
2. Enter the reporting date in `YYYY-MM-DD` (Asia/Dhaka).
3. Choose 100, 300 or 500 as the maximum number of messages inspected per configured public channel.
4. Start the workflow and download `legion-osint-public-telegram-gemini-YYYY-MM-DD`.

Artifacts: ten-section report, individual source briefs, CSV evidence register and JSON coverage summary.

### Coverage and verification limits

- Collection uses public Telegram preview pages for configured channels only.
- It does not use authenticated Telegram access or Telegram global search; it does not directly search X, Facebook, YouTube or general news websites.
- Public preview history and pagination may be incomplete or change; pages may be unavailable or rate-limited.
- Gemini structures supplied posts but is not an independent fact-checker. Treat posts as claims, label rumours and corroborate independently.
- The workflow does not fabricate a 50-brief quota.
- Artifacts are retained for 14 days; the database is temporary and analyst review state is not preserved.

A VPS is unnecessary unless continuous collection or an always-available Telegram bot becomes a requirement.
