# Legion-OSINT V8 — Reporting and triage specification

## Release intent

V8 is a data-quality release. It does not expand collection access or claim comprehensive monitoring. It improves the path from public source post to analyst review.

## V8 changes

1. **Whole-phrase keyword matching:** avoids substring matches such as the word "war" inside "award". Keyword triage remains fallible and language-limited.
2. **Typed source records:** separates physical incident leads, civil-unrest event leads, security-action leads, threat/mobilisation leads, protest announcements, political-security developments and general relevant developments.
3. **Narrower incident-candidate rule:** a relevant post becomes a candidate only when it contains a physical-event, actual unrest-action or security-action indicator. Threats and planned demonstrations remain separate record types.
4. **Bangladesh count reconciliation:** the executive assessment and Bangladesh section derive from the same metadata-filtered relevant-post set. Source-region metadata is not event geolocation.
5. **Exact-text candidate grouping:** repeated candidate text is grouped while preserving every source record. This is not semantic event resolution and does not establish independent corroboration.
6. **Temporal archive status:** each row carries an ISO date and distinguishes an existing empty archive from a missing archive. Counts are source-publication activity, not event or violence trends.
7. **TBC summary V8:** provides a paste-ready, owner-only command with no while loop, displays the reconciled counts and date labels, and does not modify .env.

## Analytical definitions

- **Collected source post:** a unique source record in the bounded daily archive.
- **Relevant source post:** a post matching at least one configured whole-phrase relevance indicator.
- **Incident-candidate source post:** a relevant post with physical-event, actual civil-unrest-action or security-action indicators.
- **Threat/mobilisation lead:** a relevant post indicating a threat or mobilisation without asserting that an attack occurred.
- **Exact-text candidate group:** two or more candidate source posts sharing the same normalized text. It is a deduplication clue only.
- **Bangladesh-relevant source post:** a relevant post whose configured source-region metadata is Bangladesh. This does not mean the event happened in Bangladesh.
- **Temporal comparison:** daily collection and triage counts from available archives, keyed by ISO reporting date. Missing archive is not zero.

## Safeguards

- All source posts remain UNVERIFIED.
- Publication time is not incident time.
- A publisher's region is not event location.
- Exact or near repetition is not independent corroboration.
- Threats, political statements and planned demonstrations are not completed attacks.
- No automated guilt, motive, affiliation, risk rating or violence forecast.
- Human review must inspect original sources, chronology, location evidence, media provenance, source independence, contradictions and uncertainty.
- Public Telegram previews and configured RSS/Atom feeds are bounded; private groups and authenticated Telegram search are not accessed.

## TBC deployment

`tbc/summary_v8_command.txt` is a manual replacement artifact. Import or paste it into the existing TBC `/summary` command only after reviewing it. GitHub commits do not update TBC. Preserve the existing `.env`, owner ID, bot working state and webhook; do not run the polling bot workflow while TBC is active.
