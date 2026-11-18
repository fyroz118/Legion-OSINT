# Free personal Telegram bot (GitHub Actions)

The repository can run the private Telegram command bot without a VPS or paid hosting.
GitHub Actions starts a short-lived worker on a five-minute schedule. Each run checks
Telegram for pending commands, processes up to 100 updates, and exits. The database and
Telegram update offset are carried forward in a GitHub Actions cache.

## Required one-time setup

In the repository, open **Settings → Secrets and variables → Actions → New repository secret**
and add:

- `TELEGRAM_BOT_TOKEN`: the token from BotFather. Never commit it or share it in chat.
- `TELEGRAM_ALLOWED_USER_IDS`: your numeric Telegram user ID. You can obtain it by messaging
  a reputable Telegram ID helper such as `@userinfobot`; enter only the numeric ID.

Optional:
- `GEMINI_API_KEY`: enables Gemini-backed `/ask` and research features that require Gemini.
  Gemini usage must stay within the provider's free allowance to avoid charges.
- Repository variable `GEMINI_MODEL`: optional model override.

Do not add these values to workflow YAML, source files, issues, or public commits.

## Enable and test

1. Open **Actions → Legion-OSINT personal Telegram bot**.
2. If GitHub asks, enable workflows for the repository.
3. Select **Run workflow** once to test immediately.
4. Open the run and inspect the **Process pending Telegram commands** step.
5. In Telegram, send `/start` to `@legion_osint_bot`. Scheduled runs may take up to five minutes
   to respond; GitHub may delay scheduled starts further.
6. Try `/status` and `/help`.

## Important limitations

- This is a best-effort, five-minute polling bot, **not** a continuously running 24/7 process.
  GitHub scheduled workflows can be delayed or skipped, so replies are not guaranteed.
- A run processes up to 100 queued Telegram updates and has a four-minute job limit.
- Long-running commands such as broad research may exceed the worker limit; use the existing
  on-demand GitHub Actions research workflow for larger jobs.
- The database and update offset are preserved in an Actions cache. Cache eviction or a failed
  run can require recovery; this is not a transactional database service.
- GitHub-hosted runner availability and free-tier terms are controlled by GitHub and can change.
- Public repository code remains public. Keep all credentials in Actions secrets only.
- The bot remains private: it accepts commands only from the configured numeric user ID in a
  private Telegram chat.
