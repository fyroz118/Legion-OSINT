# Global Telegram source policy

Legion-OSINT does not claim to monitor every Telegram channel. Telegram has no universal public directory of all channels; discovery is incomplete, public visibility does not imply reliability, and access/rate limits can change.

## Initial enabled sources
- [Bellingcat EN](https://t.me/bellingcat_en): specialist investigative OSINT; useful for investigations and verification, not a continuous breaking-news feed.
- [BNO News](https://t.me/BNONews): broad breaking-news feed; treat every item as a lead pending corroboration.

The active collector allowlist is `config/channels.json`. The wider source registry and review queue are in `config/source_registry.json`.

## Candidates requiring manual review
- [OSINTdefender](https://t.me/s/osintdefender): public page confirmed, but coverage can include granular military and weapons information. Not enabled for automated ingestion.
- [Molfar](https://t.me/molfar_global): surfaced in a third-party catalogue; direct identity and current public access require confirmation.

## Expansion standard
Enable a source only after confirming its public Telegram page and exact username, operator/affiliation where knowable, languages and geographic scope, content safety, and bias/reliability notes. Prioritize local journalists, humanitarian organizations, independent monitors, civil-society groups, and official public agencies. Do not use subscriber counts as a reliability score.

## Collection and verification
- Collect public posts only from the reviewed allowlist. Never bypass access controls or scrape private groups.
- Keep original post URLs, source identity, publication time, collection time, and original language.
- Keep social posts at `UNVERIFIED` until independent corroboration is documented.
- Distinguish incident time from publication time. Check recycled media, location claims, and attribution.
- Do not infer imminent violence from rhetoric alone.
- Exclude doxxing, private-person profiling, targeting, and granular real-time military movement or targeting data.
- Respect Telegram terms, rate limits, and applicable law.

## Why this is not “all channels”
Third-party catalogues show the scale and heterogeneity of the ecosystem. TGScope reported 88 public channels in its OSINT topic hub in October 2026. WorldMonitor documents a 56-channel feed that includes official, state-affiliated, partisan, and belligerent-party sources. These are discovery references, not safe or authoritative whitelists. Legion-OSINT reviews candidates rather than indiscriminately ingesting them.

This is a source-discovery baseline, not comprehensive global coverage. Telegram-only monitoring will miss important events; reports must be cross-checked against independent newsrooms, official statements, humanitarian data, and incident datasets.
