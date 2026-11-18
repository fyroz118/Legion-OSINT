# Legion-OSINT deployment options

## Recommended: on-demand mode without a VPS

**A continuously running server is not required** for occasional public-web research. Use the manual GitHub Actions workflow at `.github/workflows/on-demand-research.yml`. It starts an ephemeral hosted runner when manually triggered and terminates after exporting the report artifacts.

### One-time setup

1. Open the repository's **Settings → Secrets and variables → Actions**.
2. Create a repository secret named `TAVILY_API_KEY` and store the Tavily key there. Do not put secrets in workflow inputs, source files, issues, or chat.
3. No DigitalOcean account, server, Telegram API credentials, Gemini key, BotFather token, or Telethon session is required for this mode.

### Each research session

1. Open **Actions → Run Legion-OSINT on demand → Run workflow**.
2. Enter the reporting date as `YYYY-MM-DD` in Asia/Dhaka time.
3. Choose 60 queries for the standard run or 100 for expanded discovery.
4. Start the workflow and wait for completion.
5. Download the `legion-osint-YYYY-MM-DD` artifact from the completed run.

The artifact includes a ten-section preliminary discovery report, individual source briefs, a CSV lead register, and a JSON coverage summary. Results are still unverified source leads. The report deliberately does not pretend that search snippets are verified incidents or that a complete early-warning assessment has been performed.

### Limits and costs

- Tavily API credits and plan limits still apply: up to 60 or 100 basic search requests respectively, if every query executes.
- Search provider indexing is not universal access to Telegram, X, Facebook or YouTube.
- No persistent Telegram bot, scheduled collector, interactive analyst review queue, or saved incident ledger runs in this mode.
- GitHub Actions artifacts are retained for 14 days by this workflow; download and retain important outputs securely.
- The runner is temporary. Its local SQLite database is not a persistent cross-run database.
- Do not claim live monitoring, comprehensive coverage, incident verification, or 24/7 uptime.

## Optional: persistent VPS mode

Use the DigitalOcean deployment instructions below only if continuous Telegram collection or an always-available Telegram bot becomes necessary.

# Legion-OSINT cloud deployment

## Selected deployment target

The deployment target is **DigitalOcean Droplet, Singapore region, Ubuntu 24.04 LTS**. Start with the Basic Droplet plan of **1 vCPU, 2 GiB RAM, 50 GiB SSD, 2,000 GiB outbound transfer: USD $12/month** at the published list price. This is a modest pilot size for the two low-volume Python services; monitor memory and upgrade to 4 GiB if the collector, database, or research runs show resource pressure. Taxes, account-specific pricing and any optional backups are additional. Confirm the final checkout price before creating the server.

- Provider: https://www.digitalocean.com/
- Droplet pricing: https://www.digitalocean.com/pricing/droplets
- Create in Singapore for a nearby regional location; this is a practical latency choice, not a guarantee of the best route from every Bangladesh ISP.
- Use Ubuntu 24.04 LTS, regular Basic Droplet, 2 GiB RAM.
- Add an SSH public key during creation. Prefer key-only SSH; do not enable password login.
- Do not open inbound application ports. The Telegram bot uses outbound polling; collector and research use outbound connections.

**No server has been purchased or provisioned.** Provisioning requires the account owner to create the Droplet and accept its billing. Do not send provider passwords, API tokens, SSH private keys, Telegram login codes, or session files in chat.


The recommended production shape is a persistent Linux host running two Docker services:
- `bot`: private Telegram Bot API interface.
- `collector`: scheduled Telethon collection worker.

Both services share a persistent Docker volume for the SQLite database and Telethon session. Do not use ephemeral storage: the session and database must persist across restarts.

## Required deployment secrets

Set these as environment variables in the hosting provider's private service settings. Do not commit a `.env` file.

- `TELEGRAM_API_ID`
- `TELEGRAM_API_HASH`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_ALLOWED_USER_IDS` (your own numeric Telegram user ID)
- `GEMINI_API_KEY`
- `GEMINI_MODEL=gemini-2.5-flash`
- `TAVILY_API_KEY` (required only for `/research`; keep it private)
- `TAVILY_SEARCH_DEPTH=basic`
- `RESEARCH_MAX_QUERIES=60`
- `DATABASE_PATH=/app/data/legion_osint.sqlite3`
- `TELETHON_SESSION_PATH=/app/data/legion_osint_user`
- `COLLECT_INTERVAL_MINUTES=60`
- `COLLECT_LIMIT_PER_CHANNEL=100`
- `REPORT_TIMEZONE=Asia/Dhaka`

## First-time Telethon authorization

Telethon user sessions require a one-time interactive login using the account's phone number and Telegram login code (and 2FA password if enabled). This authorization cannot be completed by a bot token alone.

On a trusted host with a terminal, run the collector once interactively before starting the persistent services:

```bash
docker compose run --rm collector python -m app.collector
```

Enter the Telegram phone number and login code in the terminal prompt. Never send the code or session file to anyone. The session is stored in the persistent `legion_data` volume. Once login completes, start the services:

```bash
docker compose up -d --build
```

If the hosting provider does not provide a secure interactive terminal, do not attempt to send login codes through chat or logs. Use a trusted one-time terminal environment to create the session, then transfer it securely to the persistent host.

## Source configuration

The Telegram collector's configured public-channel list is only one supplementary source layer. It does not define global report coverage; the event-led public-web research adapter is separate. Add only reviewed, lawfully accessible public channels, and respect platform rules and access controls.

## Operational checks

- Bot: send `/start` and `/status` from the authorized private Telegram account.
- Collector: inspect host logs for successful collection and rate-limit messages.
- Database: verify new records are stored and de-duplicated.
- Gemini: use `/ask` only after records have been collected.
- Public-web research: set `TAVILY_API_KEY`, then test `/research YYYY-MM-DD`, `/briefs YYYY-MM-DD 60`, `/leads YYYY-MM-DD` and `/coverage YYYY-MM-DD`. The default is 60 queries (up to 100) and up to 10 results per query; 60 basic queries may consume up to 60 search credits. Rumour-watch results remain unverified. This is not universal access to every social platform.
- Back up the persistent volume securely.

## Important limits

This is a self-hosted starter, not a validated intelligence product. Collection coverage depends on the reviewed channel allowlist and Telegram access. Gemini can summarize records but cannot independently verify them. Do not infer imminent violence from rhetoric alone. Keep reports aggregate and avoid private-person profiling, doxxing, or sensitive operational details.


## First server hardening checklist

Before running the application:
1. Update Ubuntu packages.
2. Permit SSH in the firewall before enabling it; then allow only SSH and enable UFW. No inbound ports are required for the bot or collector.
3. Keep SSH key authentication enabled and password authentication disabled.
4. Install Docker Engine and the Docker Compose plugin from Docker's official Ubuntu instructions.
5. Clone this public repository into a dedicated directory and create `.env` from `.env.example`; set permissions to owner-only (`chmod 600 .env`).
6. Keep Docker volumes on persistent disk. Never put `.env`, Telegram session files, SQLite files, or backups in Git.
7. Configure automated security updates and a tested off-host backup of the persistent `legion_data` volume. Encrypt backups and restrict access.

Official Docker installation guide: https://docs.docker.com/engine/install/ubuntu/

## Deployment acceptance gate

Do not describe the service as operational until all checks below have passed on the actual VPS:
- `docker compose config` succeeds without printing or exposing secret values.
- Telethon one-time authorization succeeds in the VPS terminal and the session persists after a container restart.
- Both containers remain running after restart; inspect logs for collection and polling errors.
- An authorized private Telegram account can use `/start`, `/status`, and `/help`.
- A small, low-cost Tavily research test succeeds; check credit consumption before running the default 60-query session.
- Review a test lead, create a draft, attach a genuinely independent source, approve the incident, and verify that only approved incidents appear in the report.
- Restore a backup into a separate test volume and verify the database opens.
- Record a 24-hour pilot with uptime, failed jobs, source coverage, memory use, database growth, and provider/API costs.

A green GitHub Actions run validates repository code and tests only; it does not prove that any VPS, Telegram account, Gemini key, Tavily key, or live data source works.

