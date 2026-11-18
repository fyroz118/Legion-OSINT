# Legion-OSINT

A Bangladesh-priority, global OSINT monitoring and evidence-led intelligence reporting project. The target product is date-driven and event-specific: events define report coverage; configured Telegram channels are only one discovery layer.

## Reporting specification
See MASTER_PROMPT.md for the ten-section daily report structure, incident extraction fields, evidence labels, source rules, date handling, coverage disclosure and safety boundaries.

## Current architecture
- Curated public Telegram collector (Telethon) — one source adapter, not global coverage.
- Private Telegram command bot (python-telegram-bot).
- SQLite source-post store with source metadata.
- Structured incident/evidence ledger (app/incidents.py) preserving incident date, publication date, verification status, confidence, risk and source provenance.
- Gemini-assisted Q&A grounded in collected records; Gemini is not an autonomous fact-checker.
- Docker deployment scaffold for a persistent Linux host.

## Target workflow
Reporting date (Asia/Dhaka) → event-led query plan → accessible public source discovery → candidate extraction → deduplication → independent corroboration → evidence/confidence/risk assessment → ten-section report → coverage audit.

## Source priorities
Give greater discovery attention to unofficial public sources (local journalists, eyewitnesses, independent OSINT researchers, civil-society monitors, community reporters and fact-checkers). Maintain official/institutional sources and independent newsrooms as separate parallel layers. The 70:30 unofficial-to-official attention target is not a credibility score. See SOURCE_POLICY.md.

## Safety and integrity
- Collect only lawful, accessible public material; respect platform terms, rate limits and access controls.
- No private-group scraping, access-control bypass, doxxing, private-person profiling, targeting or operational assistance facilitating violence.
- Social posts are leads, not verified facts. Reposts and syndication are not independent corroboration.
- Preserve source URLs and timestamps; distinguish event time, publication time and collection time.
- Never invent sources, incidents, casualties, locations, identities or confidence.
- Explicitly disclose platform/language/geographic gaps. Do not claim comprehensive coverage.
- Early-warning assessments are aggregate and uncertainty-aware; rhetoric alone does not prove imminent violence.

## Commands currently implemented
- /status — stored post count and source mix
- /daily — recent collected posts (not yet the curated daily intelligence report)
- /bangladesh — recent Bangladesh posts
- /search <terms> — search stored post text
- /ask <question> — Gemini Q&A over stored records

Important: The ten-section research/reporting workflow is a specification and foundation, not yet a fully automated capability. The current bot does not search the open web or all X, Facebook, YouTube and Telegram content. A research/search provider and platform-specific authorized adapters are still required. No live collection, report automation, cloud deployment or 24/7 uptime is claimed.

## Setup and deployment
See CLOUD_DEPLOYMENT.md. Keep credentials in a private environment only; never commit .env, Telegram session files or API keys. A first-time Telethon user-session authorization requires secure interactive login on the host.
