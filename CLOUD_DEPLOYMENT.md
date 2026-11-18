# Legion-OSINT deployment

## Recommended: on-demand Telegram + Gemini workflow (no VPS)

The recommended mode for occasional reporting is the manual GitHub Actions workflow at `.github/workflows/on-demand-research.yml`. A temporary GitHub-hosted runner starts only when manually triggered and shuts down after the report artifacts are created.

### One-time setup

1. Obtain Telegram API ID and API hash through Telegram's official developer portal.
2. Install Python 3.11 and project dependencies on a trusted local environment.
3. Run `python scripts/export_telegram_session.py`. Complete the Telegram login in that local terminal. The script prints a Telethon StringSession.
4. Treat the session string as a full account credential. Never send it in chat, commit it, or store it in a public file. Revoke it in Telegram if exposed.
5. Open the GitHub repository's **Settings → Secrets and variables → Actions** and add:
   - `TELEGRAM_API_ID`
   - `TELEGRAM_API_HASH`
   - `TELETHON_SESSION_STRING`
   - `GEMINI_API_KEY`

Do not add these values as workflow inputs or commit them to the repository.

### Run a report

1. Open **Actions → Run Legion-OSINT on demand → Run workflow**.
2. Enter the reporting date in `YYYY-MM-DD` (Asia/Dhaka).
3. Choose the maximum recent messages inspected per configured channel: 100, 300 or 500.
4. Start the workflow and download the artifact named `legion-osint-telegram-gemini-YYYY-MM-DD`.

Artifacts:
- `daily_intelligence_report.md`: Gemini-assisted ten-section report.
- `individual_source_briefs.md`: source-specific Telegram post briefs.
- `telegram_posts.csv`: collected-post register.
- `collection_summary.json`: channel counts and errors.

### Coverage and verification limits

- This workflow uses Telethon and Gemini only. It does not use Tavily or perform general web search.
- It reads only configured, accessible public Telegram channels in `config/channels.json`; it does not cover every Telegram channel or all posts.
- The collector inspects only the most recent configured number of messages per channel and retains posts published on the requested date in Asia/Dhaka.
- The Telethon StringSession is highly sensitive. Anyone possessing it may access the associated Telegram account. Use a dedicated account if appropriate, restrict repository access, and revoke the session if compromised.
- Gemini summarises and structures supplied posts; it is not an independent fact-checker. Treat posts as claims, label rumours, and corroborate independently before publication.
- The workflow does not fabricate a 50-brief quota. If the configured sources yield fewer posts, fewer briefs are produced.
- Artifacts are retained for 14 days. The workflow uses a temporary database; analyst review state is not preserved between runs.
- The optional Telegram command bot is not started by this workflow.

## Optional persistent deployment

A VPS is not required for the on-demand workflow. A persistent Linux host is only needed if continuous Telegram collection or an always-available Telegram command bot is later desired. Do not provision a server unless that requirement changes.
