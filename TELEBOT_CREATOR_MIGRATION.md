# Legion-OSINT — Telebot Creator Migration Plan

Status: preparation in progress. This document is not proof that the TBC port is deployed or tested.

## Non-negotiable objective
A private Telegram intelligence assistant backed by a continuously expanding, unofficial-source-first public OSINT monitoring network, targeting 1,000+ channels. Bangladesh receives highest monitoring priority. Official/institutional sources remain a parallel validation layer.

The Telegram bot is the user interface. It is not the primary collection engine.

## Current architecture to preserve
- GitHub repository: source of truth for code, configuration, channel discovery, collection and report specifications.
- Hourly channel discovery workflow: candidate discovery only; candidates remain unreviewed and disabled until reviewed.
- Scheduled public Telegram collector: currently every two hours, using public Telegram preview pages for the finite enabled channel list.
- TBC: hosted Telegram interface, commands, user interaction and notifications.
- Analysis/reporting: retain evidence-first workflow and uncertainty labels.

## Migration safety
1. Preserve this repository and all existing workflows except the old bot polling worker when explicitly retired.
2. Never run the GitHub polling worker while TBC is operating the same Telegram bot. Telegram webhook delivery and getUpdates polling are mutually exclusive.
3. The GitHub bot workflow is currently manual-only. Do not dispatch it during TBC operation.
4. Keep the scheduled public collector and hourly discovery workflows running.
5. Do not put large collection jobs inside TBC commands. TBC documents a per-command execution ceiling (currently 160 seconds in its introduction); use GitHub Actions for long-running collection.
6. Do not place Telegram bot tokens, Gemini keys, TBC credentials or private user IDs in this repository, migration exports, chat messages or logs.
7. Do not import untrusted/unreviewed channel candidates into the active source list automatically.
8. Do not claim 1,000+ channels are monitored until actual successful collection coverage is measured.

## TBC implementation boundary
TBC uses TPY, a restricted Python-like runtime, not ordinary CPython. Existing Python modules cannot be uploaded and expected to run unchanged.

Use TBC for: private command interface and access control; status and coverage summaries; querying the intelligence backend; displaying daily and Bangladesh reports; search, briefs, lead review and incident workflow interactions; delivery of scheduled alerts once a reliable backend feed is implemented.

Use GitHub Actions for: public channel candidate discovery; bounded scheduled collection; data validation, deduplication and analysis jobs; durable versioned code/configuration and test workflows.

## Existing command inventory (from app/bot.py)
- /start, /help
- /status, /daily, /bangladesh, /search
- /ask, /report, /research
- /briefs, /leads, /coverage
- /reviewqueue, /reviewlead, /candidates
- /incidentdraft, /incidentqueue, /approveincident, /linklead

The existing Python implementation also has callback-button review handling. This must be reimplemented using TBC-supported inline keyboard callbacks; it is not automatically portable.

## Existing evidence model
Posts are keyed by (channel_username, message_id) and retain publication/collection timestamps, original text, source URL, language, priority region, evidence status, source class/type/affiliation and monitoring weight.

Research leads, coverage records, analyst review decisions, incident drafts and incident-source links are stored separately in SQLite. A migration must map these records explicitly; a CSV of posts alone does not migrate the full analyst history.

## Integration decision still required
Do not assume TBC can directly read GitHub Actions artifacts or GitHub's SQLite cache. Those are not stable public APIs for this purpose.

Before implementing live /daily, /search, /status and alerts, choose and test a secure data handoff: authenticated pull API from a small backend; a carefully scoped push/webhook handoff from GitHub Actions to a TBC endpoint; or another documented TBC-supported integration.

The integration must authenticate requests, validate payloads, deduplicate by source/message ID, expose collection timestamps and errors, and avoid publishing private bot data or secrets.

## Acceptance tests before cutover
1. TBC /start and /help work for the authorized owner only.
2. /status accurately reports backend freshness, configured channels, successful channels, errors and stored post counts.
3. /daily and /bangladesh return real collected records with source links and timestamps.
4. /search searches stored records, not a fabricated or static sample.
5. Research leads remain distinct from verified incidents.
6. Analyst review actions are auditable and do not automatically verify claims.
7. Scheduled collection and hourly discovery run independently of TBC command traffic.
8. Alerts are deduplicated, rate-limited and traceable to source posts.
9. A rollback path exists before disabling any working component.

## Immediate next step
Export the current TBC bot commands/data from the dashboard as a backup before importing or replacing anything. Use TBC's export function and retain the untouched original. Then build/import commands in a staged test set, without changing the active collection workflows.