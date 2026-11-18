# Legion-OSINT — Master Reporting Specification

## Current execution mode

The on-demand workflow reads **public Telegram web preview pages** for the finite channel list in `config/channels.json`, then uses **Gemini** to organise and synthesise evidence. No Telegram account session, Telegram API ID/hash, Telegram global search, Tavily or general web search is used.

Collection is limited to configured public channels and whatever history Telegram exposes through public preview pages at run time. Pagination is bounded. The workflow does not directly search X, Facebook, YouTube or news websites. Never claim comprehensive platform or global coverage.

## Reporting objective

Produce one consolidated daily intelligence report and individual source-post briefs for a user-supplied reporting date. Bangladesh receives highest priority, followed by South Asia, MENA and other regions represented in collected evidence.

Target 50+ individual source briefs when configured channels expose sufficient relevant posts. This is a target, not a quota. Never invent, duplicate, pad or inflate source records or incident counts.

## Required report structure

1. Executive Summary
2. Bangladesh Intelligence Report
3. International Conflict and Security, grouped by region only where evidence exists
4. Communal and Social Violence
5. Political Developments
6. Misinformation and Information Operations
7. Incident Register: date, country, location, category, incident, verification, confidence and source links
8. Early-Warning Assessment
9. Source and Coverage Assessment
10. Overall Intelligence Judgment

## Evidence handling

Preserve the original Telegram channel/message URL, publication timestamp in Asia/Dhaka, original text or faithful excerpt, language and regional metadata, verification status and uncertainty.

Distinguish publication date from incident date. If incident date, location, actors, casualty figures or attribution are absent, mark them unknown. Do not infer them.

Treat every post as a claim or lead, not a verified fact. Gemini is an analysis assistant, not an independent fact-checker. Reposts and copied statements are not independent corroboration. Seek separate source provenance before calling reports corroborated.

Rumours and allegations may be included with a clear **UNVERIFIED RUMOUR** or **DISPUTED** label, original source link, timestamp and known verification gaps. Inclusion does not endorse the claim. Keyword flags are review prompts, not reliable rumour classification.

## Early warning

Assess risk only from substantiated, contextual and aggregated evidence. Inflammatory rhetoric alone does not establish imminent violence. Explain uncertainty and competing explanations. Do not provide tactical details, targeting guidance or sensitive operational information.

## Source priorities and coverage disclosure

Prefer local journalists, eyewitness reporting, independent monitors, researchers, civil-society organisations and community sources as discovery leads. Maintain official/institutional sources as a parallel validation layer. Configured channel metadata is not proof of reliability or independence.

Report which configured public previews were accessible, page counts, channel errors, requested caps and date-matched post counts. State that Telegram global search and other platforms were not searched and public-preview history may be incomplete.

## Integrity and safety

- Never invent incidents, sources, URLs, quotations, statistics, casualties, identities, affiliations, motives, coordinates or trends.
- Never convert a post into a verified incident solely because Gemini summarised it.
- Do not count old reposts as new incidents or copied posts as independent corroboration.
- Do not infer private individuals' identities or profile private persons.
- Use only lawful, accessible public material; respect platform terms, rate limits and access controls.
- Do not scrape private groups, bypass access controls, doxx, target people or provide tactical assistance facilitating violence.
- Disclose missing sources, channel access failures, language gaps and collection limits.
- If evidence is insufficient, say so. Empty sections do not mean no incidents occurred.
