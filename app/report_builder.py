"""Render a clearly labelled report draft from reviewed incident-ledger entries."""
from datetime import datetime
from app.incidents import get_report_incidents

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
            lines.append(f"Ledger records: {len(incidents)}. Attached source records: {source_count}.")
            lines.append("Live platform access, languages searched, geographic coverage and inaccessible sources have not been assessed by this draft generator.")
        else:
            lines.append("No analyst narrative has been entered. Research and review this section before publication.")
        lines.append("")
    lines.extend([
        "## Publication gate", "",
        "- Do not publish until event dates, source independence, original links, conflicting claims and coverage gaps have been reviewed.",
        "- This draft generator does not search the internet, extract incidents automatically, verify claims or establish comprehensive coverage.",
    ])
    return "\n".join(lines)
