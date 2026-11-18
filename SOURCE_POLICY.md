# Global Telegram source policy

Legion-OSINT uses **both official and unofficial public Telegram sources**, with greater monitoring attention devoted to unofficial sources. The initial discovery/analyst-attention target is approximately **70% unofficial leads and 30% official/institutional sources**. This is a coverage allocation, never a credibility score or a shortcut to verification. Independent newsrooms are classified separately from government and institutional official accounts.

## Unofficial sources — priority layer

Prioritize public posts from:
- Local journalists and regional news correspondents.
- Eyewitnesses and community reporters.
- Independent OSINT investigators and researchers.
- Civil-society, human-rights, conflict-monitoring and election-monitoring groups.
- Humanitarian observers and local response organizations.
- Independent fact-checkers and media-verification researchers.
- Relevant local-language public channels with a transparent identity and track record.

These sources often provide early, geographically specific signals. Treat their posts as **leads**, not confirmed events. Record provenance, original post URL, publication time, collection time, language, claimed location, and any media provenance. Corroborate with independent sources before upgrading evidence status.

## Official and institutional sources — parallel validation layer

Monitor public channels operated by:
- Government ministries and public agencies.
- Police, fire, emergency management and public-safety agencies.
- Election commissions and courts.
- Public health and disaster-management agencies.
- International organizations and humanitarian agencies.
- Other relevant public institutions.

Official statements are primary evidence of what an institution said or announced; they are not automatically proof that every factual claim in the statement is correct. Compare official claims with independent reporting, local observers, documents and other available evidence.

## Independent media

Track established local, national and international newsrooms as a distinct source class. Do not mislabel all newsrooms as government-official sources. Consider ownership, editorial independence, access, correction practices and known political or commercial alignment.

## Monitoring allocation and source scoring

- Aim for roughly 70% of source-discovery and analyst-attention capacity on unofficial sources and 30% on official/institutional sources; adapt by region and event.
- Maintain enough independent media to triangulate both categories.
- Do not equate post volume, speed, follower count, virality or source class with credibility.
- Assess each source on identity transparency, directness of observation, historical accuracy, evidence links, correction behaviour, local expertise, independence and potential incentives/bias.
- A single source may be useful for discovery but must not be counted as multiple corroborating sources through reposts or syndication.

## Initial enabled sources

Global:
- [Bellingcat EN](https://t.me/bellingcat_en): specialist investigative OSINT; unofficial/independent investigative source.
- [BNO News](https://t.me/BNONews): independent breaking-news service; treat each item as a lead pending corroboration.

Bangladesh:
- [bdnews24.com](https://t.me/bdnews24telegram): national newsroom feed; public preview showed an owner-inactivity warning, so monitor availability and cadence.
- [Prothom Alo](https://t.me/prothomaloonline): Bengali-language national newsroom feed.
- [Rumor Scanner](https://t.me/RumorScanner): independent fact-checking initiative; inspect cited evidence.
- [The Daily Star](https://t.me/TheDailyStar): English-language national newsroom feed.

The active collector allowlist is `config/channels.json`. The wider source registry and review queue are in `config/source_registry.json`. The current starter list is not yet a balanced global source network; the 70/30 target applies to expansion and analyst attention as the registry grows.

## Candidates requiring manual review

- [OSINTdefender](https://t.me/s/osintdefender): public page confirmed, but coverage can include granular military and weapons information. Not enabled for automated ingestion.
- [Molfar](https://t.me/molfar_global): surfaced in a third-party catalogue; direct identity and current public access require confirmation.

## Expansion standard

For every candidate, verify the exact public Telegram username/page, operator or affiliation where knowable, languages, geographic scope, current activity, content safety, and bias/reliability notes. Seek local and regional unofficial sources first, then add official institutions for parallel confirmation. Never invent channel handles or activate candidates based only on directory listings.

## Collection and verification

- Collect public posts only from the reviewed allowlist. Never bypass access controls or scrape private groups.
- Keep original post URLs, source identity, publication time, collection time, and original language.
- Keep social posts at `UNVERIFIED` until independent corroboration is documented.
- Distinguish incident time from publication time. Check recycled media, location claims, and attribution.
- Do not infer imminent violence from rhetoric alone.
- Exclude doxxing, private-person profiling, targeting, and granular real-time military movement or targeting data.
- Respect Telegram terms, rate limits, and applicable law.

## Coverage limitation

Telegram has no universal public directory of all channels. Public availability does not imply reliability, and Telegram-only monitoring will miss important events. The registry is a reviewed, evolving sample—not a claim of comprehensive global coverage. Reports must be cross-checked against independent newsrooms, official statements, humanitarian data, and incident datasets.
