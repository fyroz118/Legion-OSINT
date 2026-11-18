# High-volume public-web research

Legion-OSINT's default research session runs 60 event-led search queries (maximum 100), requesting up to 10 results per query. Bangladesh is first priority, followed by the Indian subcontinent and MENA, with global searches retained. Queries include local/unofficial discovery, official/institutional checks and explicit rumour-watch terms. The approximate 70:30 split is query focus only; returned source identities are not classified automatically.

## Output model
- `/research YYYY-MM-DD` runs discovery.
- `/briefs YYYY-MM-DD [limit]` displays up to 100 individual source-lead briefs. These are source-specific items, not necessarily 100 unique incidents.
- `/leads YYYY-MM-DD` lists saved leads.
- `/coverage YYYY-MM-DD` reports regional query success/failure.
- `/report YYYY-MM-DD` creates the consolidated ten-section draft from reviewed incident-ledger records.

New leads are `UNVERIFIED` and `UNREVIEWED`. Rumour-watch items are labelled `RUMOUR_WATCH`; their claims are not facts. A rumour may be retained even when it cannot yet be corroborated, but harmful allegations should be summarized cautiously and not amplified unnecessarily. Duplicate source links are deduplicated; different sources describing the same event remain separate source briefs until an analyst consolidates the event.

## Limits and cost
At Tavily basic depth, 60 successful queries may consume up to 60 search credits per session; actual billing depends on provider rules and successful calls. The 100-query cap is a safety/cost guard. Results depend on the provider's index and ranking. This is not direct access to every Telegram channel, X, Facebook, YouTube or local-language post. Configured Telegram channels are not the global coverage boundary, but direct platform collection requires separate lawful API/access adapters. No system can guarantee every rumour or news item.

## Configuration
Set `TAVILY_API_KEY`, `TAVILY_SEARCH_DEPTH=basic` and optionally `RESEARCH_MAX_QUERIES=60` in the private host environment. Never commit keys. Search leads do not automatically become incidents or verified facts.
