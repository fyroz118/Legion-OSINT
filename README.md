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
- On-demand Telethon collection from configured, accessible public Telegram channels.
- Gemini-assisted batch analysis and synthesis into a ten-section daily report.
- Individual Telegram post briefs, CSV evidence register and JSON collection summary.
- SQLite evidence store; optional private Telegram command bot remains separate.
- No Tavily or public-web search provider is used by the on-demand workflow.

## Commands
- /status — stored Telegram post count and source mix
- /daily — recent collected Telegram posts
- /bangladesh — recent Bangladesh Telegram posts
- /search <terms> — search collected post text
- /ask <question> — ask Gemini about stored records
- /briefs YYYY-MM-DD [limit] — stored public-web source leads from the legacy research module, if any
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

Assign each source's independence group based on provenance when maintaining the ledger. A source-role label does not itself prove independence or truth. Corroboration/contradiction links require a manually assigned source-group label; groups must reflect original publisher provenance, not merely different URLs.

Review workflow records:

```text
/incidentqueue YYYY-MM-DD
/approveincident INCIDENT_ID approved rationale words...
/approveincident INCIDENT_ID rejected rationale words...
```

Approval is only permission to include an incident record in the report. It does not upgrade `verification_status`, confidence, or factual certainty. The report builder includes only `APPROVED` workflow records; `DRAFT` and `REJECTED` records are excluded. Rumours must remain explicitly labelled as unverified. Do not approve an item merely because multiple outlets repeat the same original claim.

Existing incident rows are migrated into the workflow as `DRAFT` on first initialization, so prior records are not silently published.


## On-demand mode (no VPS required)

The recommended mode for occasional use is the manual GitHub Actions workflow. It starts an ephemeral runner only when requested and stops when the job finishes; no always-on bot, DigitalOcean Droplet, Telethon login session, or Gemini key is needed for this public-web research path.

1. In the repository, open **Settings → Secrets and variables → Actions → New repository secret**.
2. Add `TAVILY_API_KEY` as a repository secret. Never put the key in source files, workflow inputs, issues, or chat.
3. Open **Actions → Run Legion-OSINT on demand → Run workflow**.
4. Enter the reporting date in `YYYY-MM-DD` (Asia/Dhaka) and choose 60 or 100 queries. A 100-query run can use up to 100 basic Tavily credits.
5. When the workflow finishes, download the `legion-osint-YYYY-MM-DD` artifact.

The artifact contains:
- `preliminary_daily_report.md` — ten-section preliminary discovery report. It is explicitly not a verified intelligence assessment.
- `individual_source_briefs.md` — individual source-lead briefs, including rumour labels.
- `source_leads.csv` — sortable source register.
- `research_summary.json` — query outcomes and coverage metadata.

The on-demand workflow uses Tavily public-web search only. It does not start the Telegram command bot or Telethon collector, and it does not provide persistent analyst-review state between runs. Every result is an unverified lead; manual corroboration remains necessary. GitHub retains the artifact for 14 days. Tavily API credits/plan limits still apply. GitHub-hosted runner availability and repository Actions settings also apply.

The VPS instructions below remain an optional path only if continuous Telegram collection or an always-available Telegram bot is wanted later.
