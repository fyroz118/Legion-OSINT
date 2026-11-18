"""Render a clearly labelled report draft from reviewed incident-ledger entries."""
from datetime import datetime
from app.incidents import get_report_incidents
from app.research import get_research_coverage, get_research_leads

SECTIONS = [
    "Executive Summary", "Bangladesh Intelligence Report",
    "International Conflict and Security", "Communal and Social Violence",
    "Political Developments", "Misinformation and Information Operations",
    "Incident Register", "Early-Warning Assessment",
    "Source and Coverage Assessment", "Overall Intelligence Judgment",
]


def _cell(value):
    return str(value or "Not established").replace("|", "\\|").replace("\n", " ")


def build_report_draft(report_date):
    datetime.strptime(report_date, "%Y-%m-%d")
    incidents = get_report_incidents(report_date)
    lines = [
        f"# Legion-OSINT Daily Intelligence Report — {report_date}", "",
        "**Reporting timezone:** Asia/Dhaka (UTC+6)",
        "**Status:** DRAFT FROM INCIDENT LEDGER — not a live web-researched or independently verified report.",
        "",
        "This draft contains only incidents already entered in the local evidence ledger. Empty sections are not evidence that no events occurred.", "",
    ]
    for section in SECTIONS:
        lines.extend([f"## {section}", ""])
        if section == "Incident Register":
            lines.extend([
                "| Date | Country | Location | Category | Incident | Verification | Confidence | Sources |",
                "|---|---|---|---|---|---|---|---|",
            ])
            if incidents:
                for item in incidents:
                    links = "<br>".join(
                        f"[{_cell(src.get('source_name') or 'Source')}]({src['source_url']})"
                        for src in item["sources"]
                    ) or "No source attached"
                    lines.append(
                        f"| {_cell(item.get('incident_datetime') or report_date)} | {_cell(item['country'])} | "
                        f"{_cell(item.get('location_text') or item.get('admin2') or item.get('admin1'))} | "
                        f"{_cell(item['category'])} | {_cell(item['description'])} | "
                        f"{_cell(item['verification_status'])} | {_cell(item['confidence'])} | {links} |"
                    )
            else:
                lines.append("| — | — | — | — | No incidents entered in ledger | — | — | — |")
        elif section == "Bangladesh Intelligence Report":
            local = [x for x in incidents if x["country"].strip().lower() in {"bangladesh", "bd"}]
            lines.append(f"{len(local)} Bangladesh incident record(s) are currently in the ledger.")
            lines.append("Review district/upazila coverage, delayed reporting and conflicting accounts before publication.")
        elif section == "Source and Coverage Assessment":
            source_count = sum(len(x["sources"]) for x in incidents)
            lines.append(f"Ledger records: {len(incidents)}. Attached incident-source records: {source_count}.")
            leads = get_research_leads(report_date, limit=1000)
            coverage = get_research_coverage(report_date)
            lines.append(f"Public-web discovery leads saved: {len(leads)}.")
            focus_counts = {}
            for lead in leads:
                focus = lead.get("source_focus") or "unknown"
                focus_counts[focus] = focus_counts.get(focus, 0) + 1
            rumour_count = sum(1 for lead in leads if lead.get("claim_type") == "RUMOUR_WATCH")
            lines.append(f"Rumour-watch leads: {rumour_count} (unverified claims, not established events).")
            review_counts = {}
            source_class_counts = {}
            for lead in leads:
                review = lead.get("review_status") or "unknown"
                source_class = lead.get("source_class") or "unknown"
                review_counts[review] = review_counts.get(review, 0) + 1
                source_class_counts[source_class] = source_class_counts.get(source_class, 0) + 1
            if review_counts:
                lines.append("Analyst review status: " + ", ".join(
                    f"{key}: {value}" for key, value in sorted(review_counts.items())) + ".")
            if source_class_counts:
                lines.append("Analyst-assigned source classes (not inferred from domain): " + ", ".join(
                    f"{key}: {value}" for key, value in sorted(source_class_counts.items())) + ".")
            if focus_counts:
                lines.append("Search-focus distribution (not actual source classification): " +
                             ", ".join(f"{key}: {value}" for key, value in sorted(focus_counts.items())) + ".")
            if coverage:
                for row in coverage:
                    lines.append(f"- {row['region']}: {row['status']} — {row['query_count']} query(s), {row['result_count'] or 0} result(s).")
            else:
                lines.append("No public-web research coverage log exists for this date.")
            lines.append("This audit covers only configured search-provider queries. It does not establish direct access to X, Facebook, YouTube or all Telegram content; local-language coverage beyond configured queries remains incomplete.")
        else:
            lines.append("No analyst narrative has been entered. Research and review this section before publication.")
        lines.append("")
    lines.extend([
        "## Publication gate", "",
        "- Do not publish until event dates, source independence, original links, conflicting claims and coverage gaps have been reviewed.",
        "- This draft generator does not search the internet, extract incidents automatically, verify claims or establish comprehensive coverage.",
    ])
    return "\n".join(lines)
