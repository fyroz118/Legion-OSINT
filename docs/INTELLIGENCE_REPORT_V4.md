# Legion-OSINT Intelligence Report V4

## Purpose

The daily report is a deterministic triage digest of configured public Telegram preview posts and public RSS/Atom headlines and excerpts. It is not an automated verification system or a substitute for analyst review.

## V4 improvements

1. **Relevance filtering:** source posts are triaged against explicit conflict, political-security, civil-unrest, communal-risk, humanitarian, infrastructure, public-health and disaster keyword groups. Unrelated posts are excluded from the report's selected lead lists but remain in the underlying daily archive.
2. **Bangladesh-priority review:** Bangladesh-relevant posts are selected first and separated into category counts. District names are extracted only when explicitly mentioned in the text. These are text mentions, not geolocation.
3. **Incident-candidate extraction:** posts with both a relevant category and physical-event indicators enter a candidate queue. They remain unverified source posts, not deduplicated incidents.
4. **Repost analysis:** exact normalized text repetition is grouped. Same-publisher repetition is distinguished from cross-publisher repetition. Cross-publisher repetition is not assumed to be independent corroboration.
5. **Seven-day comparison:** current and previous daily archives are compared using collected-post, relevant-post, incident-candidate-post and Bangladesh-relevant-post counts. These are source-volume indicators, not incident rates, risk scores or forecasts.
6. **Telegram delivery:** the TBC command splits messages at line boundaries, avoids cutting words and URLs, and caps delivery to 25 messages.

## Analytical cautions

- Relevance scoring is rule-based keyword triage. It can produce false positives and false negatives, especially across languages, transliteration and short excerpts.
- Publication time is not incident time.
- Multiple posts may refer to one event; one post may contain several claims.
- Repeated text does not establish independent sourcing.
- Source class and affiliation are descriptive metadata and may be incomplete or self-asserted.
- A district-name mention is not verified geolocation.
- Empty or missing archive days do not establish that no events occurred.
- Do not infer perpetrator identity, guilt, religious motive, coordination or imminent violence from keyword matches.
- A human analyst must inspect original sources, verify date and location, assess media provenance, compare independent sources, and document confidence and uncertainty.

## Report output

The expanded JSON report is published at:

docs/feed/archive/YYYY-MM-DD/intelligence_report.json

The daily source archive remains at:

docs/feed/archive/YYYY-MM-DD.json

The Telebot Creator command reads the expanded report and does not substitute the compact summary when the expanded report is missing.
