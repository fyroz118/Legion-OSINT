# Legion-OSINT V12 — Bangladesh Recall and Claim-Precision Release

## Purpose
V12 is a bounded correction release focused on the two principal defects observed in the V11 report: missed Bengali-language Bangladesh civil-unrest leads and false physical-incident classifications caused by broad conflict/commentary wording.

## Changes
- Adds Bengali-language phrase triggers for protest, demonstration, blockade, labour action, clashes, arrests, communal targeting, injuries, fatalities and selected infrastructure disruptions.
- Separates broad relevance matches from event-action indicators. A protest mention may enter a review queue without automatically becoming a completed incident candidate.
- Removes the generic word "bombing" from the physical-event indicator list and adds more explicit action phrases.
- Adds contextual commentary indicators for political statements, seminars and military analysis. Such context suppresses incidental keyword hits unless high-specificity real-world event language is also present.
- Retains multi-label claims: a source post may contain both an alleged physical event and a separate threat/preparation claim.
- Displays all nine configured monitoring regions, including regions with zero relevant leads.
- Reports threat/preparation claims including overlaps separately from threat/preparation-only posts.
- Reports the selected source-record display count and omitted count explicitly.
- Adds regression tests for Bengali-language protest detection, commentary false positives, V12 schema versions and all-region display.

## Interpretation rules
- Bengali or English keyword matches are review leads, not verified incidents.
- A protest announcement, mobilisation notice, threat, or preparation statement is not a completed physical incident.
- Commentary suppression is deterministic phrase logic, not semantic understanding; false positives and false negatives remain possible.
- Source-post counts are not incident counts. Reposts are not independent corroboration.
- Monitoring-region metadata and district-name mentions are not geolocation.
- No motive, perpetrator, affiliation, central direction, imminent violence or risk rating is inferred.
- Provisional lead IDs identify source posts. V12 does not automatically merge paraphrased reports into unique incidents; event-level grouping remains an analyst task to avoid unsafe false merges.
- The Bangladesh excluded-post sample is an audit aid, not a statistically representative sensitivity estimate.

## Deployment boundary
The collector/publisher writes V12 archives after its next successful run. The TBC command in `tbc/summary_v12_command.txt` refuses archives whose `report_version` is not 12. GitHub publication does not deploy a command into Telebot Creator. Replace only the existing `/summary` command manually after a V12 archive exists. Preserve `.env`, OWNER_IDS, FEED_URL, webhook configuration and alert settings. Do not run the personal Telegram bot workflow while TBC is active.

## Validation boundary
Regression tests were added, but no successful GitHub Actions result or live Telebot Creator runtime test has been confirmed for this release. Do not describe V12 as fully validated or deployed until those checks are completed.
