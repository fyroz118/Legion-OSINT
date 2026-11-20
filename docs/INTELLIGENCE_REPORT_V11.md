# Legion-OSINT V11 — Multi-Label Claim and Data-Quality Validation

## Purpose

V11 is a precision and data-quality update to the deterministic public-source triage pipeline. It does not verify incidents, infer perpetrators or motives, estimate conflict intensity, or forecast violence.

## V11 changes

1. **Multi-label claim classification.** A source post can carry more than one claim type: physical incident, civil unrest, security action, and threat/preparation. Preparation language no longer overrides a separate physical-event indicator.
2. **Preparation-only relevance.** Explicit launch/strike-preparation phrases can enter the review queue without being counted as completed incident candidates.
3. **Bangladesh false-negative audit.** The report counts excluded Bangladesh posts and displays a bounded sample of up to 30 excluded records for manual review. This is a review sample, not a statistically representative sensitivity estimate.
4. **Provisional lead identifiers.** Each candidate source post receives a stable report-date-scoped provisional lead ID. The system does not merge posts into a unique incident without validated event-level location and incident-time evidence.
5. **Temporal comparability.** Current reporting days are labelled partial when the report is generated on the same local calendar date. Partial-day totals are explicitly not comparable with full-day archives. Historical archive presence does not prove complete collection.
6. **TBC summary update.** The V11 /summary command displays overlapping claim categories, provisional lead IDs, Bangladesh audit counts and temporal-status labels. It has no while loop.

## Interpretation rules

- Candidate source posts are not unique incidents.
- A provisional lead ID is a source-post tracking identifier, not an incident ID.
- Multiple claim-type counts may overlap.
- Exact-text repetition is not incident deduplication or independent corroboration.
- Monitoring-region metadata is not event geolocation.
- Publication time is not incident time.
- District-name matches are text mentions, not verified locations.
- An excluded-post sample helps identify possible false negatives but cannot establish classifier sensitivity on its own.
- Missing archives are not zero-event days; archive availability does not prove complete coverage.
- Every candidate requires original-source review, chronology and location assessment, media provenance checks, source-chain analysis and independent corroboration where possible.

## Files

- Collector and report generator: scripts/publish_tbc_feed.py
- Regression tests: tests/test_publish_tbc_feed.py
- Manual TBC command: tbc/summary_v11_command.txt
- TBC deployment instructions: tbc/README.md

## Deployment boundary

GitHub commits and successful Actions runs do not deploy commands into Telebot Creator. Replace only the existing /summary command manually. Preserve .env, OWNER_IDS, FEED_URL and the active TBC webhook. Do not dispatch the personal Telegram bot workflow while TBC is active. Alerts remain disabled unless explicitly enabled by the owner.

## Validation boundary

Automated regression tests validate deterministic code behaviour on test cases. They do not establish real-world precision, recall, Bangladesh-language sensitivity, source reliability or incident verification. Those require a manually labelled evaluation dataset and analyst review.