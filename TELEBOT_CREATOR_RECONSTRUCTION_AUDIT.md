# Legion-OSINT — TBC Reconstruction Audit

Status: source audit completed; TBC port not yet deployed. This document records what was recovered from the current `main` branch without changing or disabling existing workflows.

## 1. Recovered command surface

The existing Python bot registers these commands:

- `/start`, `/help`, `/status`
- `/daily`, `/bangladesh`, `/search`, `/ask`
- `/report`, `/research`, `/briefs`, `/leads`, `/coverage`
- `/reviewqueue`, `/reviewlead`, `/candidates`
- `/incidentdraft`, `/incidentqueue`, `/approveincident`, `/linklead`
- Inline lead-review callbacks: reviewed (not verification) and rejected.

Source of truth: `app/bot.py`. The one-shot GitHub polling worker mirrors this command registry in `app/bot_action_worker.py`.

## 2. Existing implementation map

| Existing file | Responsibility | TBC migration treatment |
|---|---|---|
| `app/bot.py` | Telegram command routing, private-chat allowlist, command UX | Rewrite as TPY commands; do not upload CPython source |
| `app/database.py` | SQLite post store, deduplication, search and source-mix counts | Replace TBC-facing reads with authenticated backend data contract |
| `app/research.py` | Public-web research leads, query coverage, analyst review and candidate suggestions | Keep heavy research in GitHub Actions; expose bounded read/review API |
| `app/incidents.py` | Incident/evidence ledger, source provenance, verification/confidence/risk fields | Keep durable ledger in backend; expose explicit analyst actions |
| `app/incident_workflow.py` | Draft/approve/reject workflow and report inclusion gate | Preserve approval ≠ verification distinction |
| `app/report_builder.py` | Daily report from explicitly approved incident records | Generate in backend; TBC displays report chunks/links |
| `app/gemini_assistant.py` | AI question answering over stored records | Optional analysis adapter; model output is not independent verification |
| `app/collector.py`, `scripts/collect_public_telegram.py` | Public Telegram preview collection | Remain in scheduled GitHub workflow |
| `scripts/discover_telegram_channels.py` | Public channel candidate discovery | Remain in scheduled GitHub workflow; candidates stay disabled until reviewed |

## 3. Workflow safety status

- `public-telegram-collection.yml` remains scheduled every two hours and uploads the latest collection artifact for seven days.
- `discover-telegram-channels.yml` remains the scheduled candidate-discovery workflow.
- `personal-telegram-bot.yml` is manual-only. It uses Telegram `getUpdates` polling and deletes a webhook before polling. **Do not dispatch it while TBC is active.**
- No existing workflow was edited or disabled in this reconstruction audit.

## 4. Data and state findings

The Python system stores more than Telegram post rows. Its SQLite state includes posts, research leads, research query coverage, analyst review decisions, incidents, incident-source provenance and incident workflow decisions.

A collection CSV/artifact is not a complete backup of this analyst history. The GitHub repository contains code/configuration but does not itself prove that the current SQLite cache or Actions cache contains a complete, durable analyst database. No historical database migration is claimed.

Post identity is deduplicated by `(channel_username, message_id)`. Preserve original source URL, publication time, collection time, language, region, source class/type/affiliation, monitoring weight and evidence status.

## 5. Required TBC/backend contract before live commands

Do not make TBC commands pretend to query GitHub Actions artifacts or SQLite directly. A documented, authenticated handoff is required.

Minimum read endpoints:
- health/status: backend timestamp, latest successful collection timestamp, configured/enabled source count, successful/failed source count, stored post count, coverage gaps;
- posts: bounded page, optional region and keyword filters, stable cursor;
- research leads and query coverage: bounded date-scoped retrieval;
- report: generated report text or document link and generation timestamp.

Minimum write endpoints:
- analyst lead review (reviewed/rejected/duplicate, source class, rationale, duplicate reference);
- incident draft and explicit inclusion decision;
- source-to-incident provenance link.

Security and correctness:
- Authenticate every request; use a scoped secret stored only in TBC and GitHub Actions secrets.
- Validate method, payload schema, field lengths, dates and allowed enum values.
- Deduplicate using stable source/message identifiers and make writes idempotent.
- Never expose GitHub Actions tokens, Telegram bot tokens, Gemini keys, TBC credentials or private user IDs in source files/logs.
- Restrict analyst write operations to the owner; default all new leads/incidents to unverified.
- Keep approval for report inclusion separate from verification/confidence.
- Include freshness timestamps and errors; do not report stale data as current.
- TBC commands must be short, bounded and compatible with the platform's TPY sandbox/time ceiling.

## 6. Port order and acceptance gates

1. TPY smoke-test package: `/start`, `/help`, owner-only access gate, safe configuration check.
2. Integration smoke test: authenticated health/status read only; verify failure handling and freshness.
3. Read commands: `/status`, `/daily`, `/bangladesh`, `/search`, `/coverage`, `/leads`, `/briefs`.
4. Analyst workflow: `/reviewqueue`, `/reviewlead`, callback review, `/candidates`, incident commands and auditable decisions.
5. Reports and optional AI: `/report`, `/ask`, `/research` (trigger a backend job rather than running long research inside TBC).
6. Alerts: deduplicated, rate-limited, source-linked, and only after end-to-end validation.
7. Cutover: only after all acceptance tests pass. Keep the old manual-only polling workflow as a disabled-by-usage rollback path; never run it concurrently with TBC.

## 7. Current blocker

The TBC dashboard export action is currently not producing a downloadable file for the owner. Reconstruction is therefore based on the repository's live source files, not an export of TBC's current dashboard state. Existing TBC-only commands or dashboard data cannot be inferred from GitHub and must be checked in TBC before any import/overwrite.

## 8. Explicit non-claims

- No TBC command package has been imported or tested in the live bot yet.
- No live backend/API handoff has been configured or tested.
- No complete SQLite analyst-history backup has been recovered.
- The 1,000+ public-channel network is a target, not current verified monitoring coverage.
