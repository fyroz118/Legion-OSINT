# High-volume public-web research adapter

Legion-OSINT uses Tavily Search API as its first configurable public-web discovery provider.

## Session target and workflow
- Default discovery plan: 60 queries (maximum 100), up to 10 results per query.
- Aim: produce 50+ individual source-lead briefs when returned evidence supports that volume. This is a target, not a quota; never pad with duplicates or invented events.
- Geographic priority: Bangladesh, the Indian subcontinent, Middle East/North Africa, then other global regions.
- The default query allocation is approximately 70% unofficial/local/public-eyewitness discovery and 30% official/institutional discovery. This measures query attention only. A domain's actual source class remains unknown until reviewed.
- Rumour-watch queries deliberately seek unconfirmed claims, viral posts and fact-checks. These results are tagged RUMOUR_WATCH leads, not confirmed rumours or facts.
- Search is event/theme-driven. The configured Telegram channel list is not the boundary of report coverage.

## Individual briefs
Use /briefs YYYY-MM-DD [limit] to render up to 100 individual source-lead briefs. Each brief preserves title, region, publication timestamp, source URL, source class (unknown until reviewed), query focus and snippet. A brief describes what a source reported; it does not establish that the event occurred. Multiple sources about one event may produce multiple source briefs and must be consolidated during incident analysis.

## Limitations
- This is broad public-web discovery, not universal internet or social-platform surveillance.
- X, Facebook, YouTube and Telegram content may appear only if indexed/surfaced by the provider; direct platform APIs/adapters require separate permissions and integration.
- Search engines can miss local-language posts, deleted content, closed groups and unindexed websites.
- Search result ranking is not verification. Rumours must remain UNVERIFIED/DISPUTED until corroborated; preserve their original wording/context and never repeat harmful allegations as established facts.
- Provider publication date is not incident date. Undated items are retained with date unknown.
- Similar headlines, syndicated stories and reposts are not independent corroboration.
- Never publish private personal data, doxxing, private-person profiling, targeting, tactical targeting details or exploitable security information.

## Configuration
Set private environment variables on the deployment host:
- TAVILY_API_KEY — required.
- TAVILY_SEARCH_DEPTH — basic by default; advanced uses more credits.
- RESEARCH_MAX_QUERIES — default 60, maximum 100.

At 60 basic queries, a session may consume up to 60 basic search credits (subject to provider billing and query execution). At 100 queries, up to 100. Each query can return up to 10 results; this is not a guarantee of 600 or 1,000 unique leads.

## Commands
- /research YYYY-MM-DD — run the expanded discovery session.
- /briefs YYYY-MM-DD [limit] — display individual source-lead briefs (default 60, maximum 100).
- /leads YYYY-MM-DD — list candidate source links.
- /coverage YYYY-MM-DD — show query success/failure and regional result counts.
- /report YYYY-MM-DD — generate the consolidated ten-section draft from analyst-reviewed incident-ledger entries.

The consolidated report still requires review, event deduplication, independent corroboration, incident-date assessment, and analyst judgment. The research adapter does not automatically verify or promote leads into incidents.
