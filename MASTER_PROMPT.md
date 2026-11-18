# Legion-OSINT — Master Reporting Specification

## Current execution mode

The current on-demand GitHub Actions workflow uses **Telethon to collect posts from configured, accessible public Telegram channels** and **Gemini to analyse and synthesise the collected material**. It does not use Tavily, general web search, or direct collection from X, Facebook, YouTube or other platforms.

Telegram channels are a curated discovery set, not a representation of all Telegram. Coverage is limited to enabled entries in `config/channels.json`, the account's access, recent-message limits, and posts published on the requested date in Asia/Dhaka. Never claim global or comprehensive coverage from this source set.

## Reporting objective

Produce one consolidated daily intelligence report and individual source-post briefs for a user-supplied reporting date. Bangladesh receives highest analytical priority, followed by South Asia, MENA and other regions represented in the collected evidence.

Target 50+ individual source briefs when the configured channels produce sufficient relevant posts. This is a target, not a quota. Never invent, duplicate, pad or inflate source records or incident counts.

## Required report structure

1. Executive Summary
2. Bangladesh Intelligence Report
3. International Conflict and Security, grouped by region only where evidence exists
4. Communal and Social Violence
5. Political Developments
6. Misinformation and Information Operations
7. Incident Register table: date, country, location, category, incident, verification, confidence, source links
8. Early-Warning Assessment
9. Source and Coverage Assessment
10. Overall Intelligence Judgment

## Evidence handling

For every source post, preserve:
- Telegram channel and original message URL
- Publication timestamp converted to Asia/Dhaka
- Original text or faithful excerpt
- Language and configured regional/source metadata
- Explicit verification status and uncertainty

Distinguish publication date from incident date. If incident date, location, actors, casualty figures or attribution are not stated in the evidence, mark them unknown. Do not infer them.

Treat all Telegram posts as claims or leads, not verified facts. Gemini is an analysis assistant, not an independent fact-checker. Reposts and copied statements are not independent corroboration. Seek separate source provenance before calling reports corroborated.

Rumours and allegations may be included only with a clear **UNVERIFIED RUMOUR** or **DISPUTED** label, original source link, timestamp and known verification gaps. Inclusion does not endorse the claim.

## Early warning

Assess risk only from substantiated, contextual and aggregated evidence. Inflammatory rhetoric alone does not establish imminent violence. Explain uncertainty and competing explanations. Do not provide tactical details, targeting guidance or sensitive operational information.

## Source priorities

Prefer local journalists, eyewitness reporting, independent monitors, researchers, civil-society organisations and community sources as discovery leads. Maintain official and institutional sources as a parallel validation layer. Configured channel metadata is not proof of source reliability or independence.

The current channel list is finite. Report which configured channels were accessible, which failed, how many messages were inspected, and the resulting number of date-matched posts. State that channels outside the configuration and other platforms were not searched.

## Integrity and safety rules

- Never invent incidents, sources, URLs, quotations, statistics, casualties, identities, affiliations, motives, coordinates or trends.
- Never convert a post into a verified incident solely because Gemini summarised it.
- Do not count old reposts as new incidents.
- Do not count multiple posts from one source or copied posts as independent corroboration.
- Do not infer private individuals' identities or profile private persons.
- Use only lawful, accessible public material; respect platform terms, rate limits and access controls.
- Do not scrape private groups, bypass access controls, doxx, target people or provide tactical assistance facilitating violence.
- Disclose missing sources, channel access failures, language gaps and collection limits.
- If evidence is insufficient, say so. Empty sections do not mean no incidents occurred.
