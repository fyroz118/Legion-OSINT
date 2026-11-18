# Legion-OSINT

A Bangladesh-priority, global OSINT monitoring and evidence-led intelligence reporting project. Events define report coverage; configured Telegram channels are only one discovery input.

## Reporting model
- Target 50+ individual source-lead briefs per research session when evidence supports it; never pad the count.
- One consolidated ten-section daily intelligence report is generated from the reviewed incident ledger.
- Bangladesh first, then the Indian subcontinent and Middle East/North Africa, with other world regions included.
- Explicit rumour/unverified-claim discovery. Rumour-watch results remain UNVERIFIED until independently assessed.
- Default query-attention target is approximately 70% unofficial/local/public-eyewitness discovery and 30% official/institutional discovery. This is not source classification or a credibility score.

See MASTER_PROMPT.md for the full specification.

## Architecture
- Public-web search adapter (Tavily) for event/theme-led discovery.
- Curated public Telegram collector (Telethon) as one additional source layer, not a channel whitelist defining all coverage.
- Private Telegram command bot.
- SQLite post, research-lead and incident/evidence ledgers.
- Gemini-assisted Q&A grounded in collected records; Gemini is not an autonomous fact-checker.
- Docker deployment scaffold for a persistent Linux host.

## Commands
- /status — stored Telegram post count and source mix
- /daily — recent collected Telegram posts
- /bangladesh — recent Bangladesh Telegram posts
- /search <terms> — search collected post text
- /ask <question> — ask Gemini about stored records
- /research YYYY-MM-DD — expanded date-scoped public-web discovery (default 60 queries)
- /briefs YYYY-MM-DD [limit] — up to 100 individual source-lead briefs (default 60)
- /leads YYYY-MM-DD — candidate source links
- /coverage YYYY-MM-DD — regional query success/failure and result counts
- /reviewqueue YYYY-MM-DD — retrieve unreviewed leads with one-tap review/reject controls
- /candidates YYYY-MM-DD [limit] — extract conservative unverified event candidates and title-similarity suggestions
- /reviewlead ID reviewed|rejected|duplicate [source_class] [duplicate_ID] — record an explicit decision
- /linklead LEAD_ID INCIDENT_ID [lead|corroboration|contradiction] — attach a reviewed source to an existing incident
- /report YYYY-MM-DD — consolidated ten-section draft from reviewed incident-ledger entries

## Critical limitations
This does not provide universal access to every news item or every post on Telegram, X, Facebook or YouTube. Public social material may appear only when indexed/surfaced by the provider; direct platform APIs require separate access and integration. Search results are source leads, not automatically distinct incidents or verified facts. New leads enter an UNREVIEWED queue; source class is never inferred from a domain. Candidate extraction uses only source title/snippet and preserves unknown incident date, precise location and actors; all candidates remain UNVERIFIED. Similar-title scoring is only a duplicate-review hint and never merges leads. A lead must be marked REVIEWED and assigned an analyst-reviewed source class before it can be linked to an incident already created in the ledger; this workflow never auto-creates or verifies an incident. Multiple briefs may describe one event. Deduplicate and corroborate before counting unique incidents or publishing judgments. Provider publication dates do not establish incident dates.

A default 60-query basic session may consume up to 60 basic search credits. It can return fewer than 50 useful or unique leads. Volume is a target, never a reason to fabricate or amplify harmful allegations.

## Safety and integrity
- Use only lawful, accessible public material; respect terms, rate limits and access controls.
- No private-group scraping, access-control bypass, doxxing, private-person profiling, targeting or tactical assistance facilitating violence.
- Preserve source URLs and timestamps; distinguish event, publication and collection dates.
- Treat rumours and social posts as unverified claims. Clearly label them; do not state allegations as fact.
- Reposts and syndication are not independent corroboration.
- Never invent sources, incidents, casualties, locations, identities or confidence.
- Disclose platform, language and geographic gaps. Do not claim comprehensive coverage.

## Setup
See CLOUD_DEPLOYMENT.md. Set TAVILY_API_KEY, TELEGRAM_BOT_TOKEN and TELEGRAM_ALLOWED_USER_IDS in private deployment environment variables. Never commit credentials or Telegram session files. No live search, cloud deployment or 24/7 uptime is claimed until credentials and runtime are configured and tested.

## Analyst incident workflow

The incident ledger is human-gated. A source lead must first be marked `REVIEWED` and assigned an analyst-reviewed source class. Then create an incident draft:

```text
/incidentdraft LEAD_ID INCIDENT_ID COUNTRY CATEGORY SOURCE_GROUP description words...
```

Use a stable source-group label for the original publisher/outlet (for example `local-outlet-a`). This is a manual independence assessment; syndicated copies of one original report must not be counted as independent corroboration. The command creates a `DRAFT` incident with `UNVERIFIED` status and attaches the reviewed lead as its first source.

Attach further reviewed sources to the existing incident:

```text
/linklead LEAD_ID INCIDENT_ID corroboration
/linklead LEAD_ID INCIDENT_ID contradiction
```

Assign each source's independence group based on provenance when maintaining the ledger. A source-role label does not itself prove independence or truth.

Review workflow records:

```text
/incidentqueue YYYY-MM-DD
/approveincident INCIDENT_ID approved rationale words...
/approveincident INCIDENT_ID rejected rationale words...
```

Approval is only permission to include an incident record in the report. It does not upgrade `verification_status`, confidence, or factual certainty. The report builder includes only `APPROVED` workflow records; `DRAFT` and `REJECTED` records are excluded. Rumours must remain explicitly labelled as unverified. Do not approve an item merely because multiple outlets repeat the same original claim.

Existing incident rows are migrated into the workflow as `DRAFT` on first initialization, so prior records are not silently published.
