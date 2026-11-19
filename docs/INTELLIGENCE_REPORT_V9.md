# Legion-OSINT Intelligence Report V9

## Purpose

The daily report is a deterministic triage digest of configured public Telegram preview posts and public RSS/Atom headlines and excerpts. It is not an automated verification system or a substitute for analyst review.

## V9 precision-first changes

1. **Narrower relevance rules:** generic words such as "military", "army", "war", "attack", "arrested" or "protest" alone are not enough to label a post relevant. Rules require more specific phrases and event contexts.
2. **Separate event-action evidence:** a source post may describe a political development or threat without describing a completed physical event. Threats and mobilisation notices are not incident candidates unless a separate explicit event-action phrase is present.
3. **Entertainment false-positive guard:** explicit gaming, film, fashion and sports contexts suppress incidental phrase matches unless a strong real-world event phrase is also present.
4. **Transparent triage fields:** report records include category reasons, event-action indicators, threat indicators, non-event context indicators and a record type for analyst review.
5. **Candidate display reconciliation:** total candidate source posts, displayed candidate records and records omitted by the 100-record display cap are separate fields. Candidate posts are not unique incidents.
6. **Regional reconciliation:** a complete regional source-post count table is published, including regions with no relevant leads; the report records whether regional totals reconcile to the daily archive.
7. **Location semantics:** monitoring-region metadata is not treated as event location. Named district references are text mentions only, not verified geolocation.
8. **Regression tests:** tests cover obvious entertainment and generic-commentary false positives, explicit physical/unrest/security actions, and threat-only language.

## Analytical cautions

- Rules remain deterministic and English-phrase dependent; false positives and false negatives remain possible, especially across Bangla, transliteration and short excerpts.
- A phrase match is not verification. Human review must inspect the original source and context.
- Publication time is not incident time.
- Multiple posts may refer to one event; one post may contain several claims.
- Repeated text does not establish independent sourcing.
- Source class, affiliation and monitoring-region metadata may be incomplete or inaccurate.
- District-name mentions are not geolocation.
- Empty or missing archive days do not establish that no events occurred.
- Do not infer perpetrator identity, guilt, religious motive, coordination or imminent violence from keyword matches.
- Analysts must verify date and location, assess media provenance, compare independent sources, and document confidence and uncertainty.

## Report output

The expanded JSON report is published at:

`docs/feed/archive/YYYY-MM-DD/intelligence_report.json`

The daily source archive remains at:

`docs/feed/archive/YYYY-MM-DD.json`

The Telebot Creator command reads the expanded report and does not substitute the compact summary when the expanded report is missing.
