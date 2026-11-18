"""Run Legion-OSINT as a one-shot public-web research job.

All returned records remain source leads. This script does not verify incidents
or infer incident dates, actors, casualty figures, or risk levels.
"""
import csv
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

from app.research import run_research, get_research_leads, get_research_coverage

def clean(value):
    return str(value or "Not supplied").replace("|", "\\|").replace("\n", " ").replace("\r", " ")

def main():
    if len(sys.argv) not in (2, 3):
        raise SystemExit("Usage: python scripts/run_on_demand.py YYYY-MM-DD [max_queries]")
    report_date = sys.argv[1]
    datetime.strptime(report_date, "%Y-%m-%d")
    max_queries = int(sys.argv[2]) if len(sys.argv) == 3 else int(os.getenv("RESEARCH_MAX_QUERIES", "60"))
    if not 1 <= max_queries <= 100:
        raise SystemExit("max_queries must be between 1 and 100")
    if not os.getenv("TAVILY_API_KEY", "").strip():
        raise SystemExit("TAVILY_API_KEY is not configured in the private workflow secrets")

    summary = run_research(report_date, max_queries=max_queries, max_results=10)
    leads = get_research_leads(report_date, limit=1000)
    coverage = get_research_coverage(report_date)
    out = Path(os.getenv("REPORT_OUTPUT_DIR", "output")) / report_date
    out.mkdir(parents=True, exist_ok=True)

    with (out / "source_leads.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        fields = ["id", "report_date", "region", "title", "source_url", "domain",
                  "published_date", "claim_type", "source_focus", "source_class",
                  "review_status", "snippet"]
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(leads)

    (out / "research_summary.json").write_text(
        json.dumps({"summary": summary, "coverage": coverage, "lead_count": len(leads)},
                   ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        f"# Legion-OSINT Source Briefs — {report_date}", "",
        "**Timezone:** Asia/Dhaka (UTC+6). **Evidence status:** all results are unverified source leads.",
        "**Important:** publication date is not proof of incident date. Multiple results may refer to one event.",
        ""
    ]
    for i, lead in enumerate(leads, 1):
        label = " — UNVERIFIED RUMOUR" if lead.get("claim_type") == "RUMOUR_WATCH" else ""
        lines += [f"## Brief {i:03d}{label}", "",
                  f"- **Region:** {clean(lead.get('region'))}",
                  f"- **Title:** {clean(lead.get('title'))}",
                  f"- **Published:** {clean(lead.get('published_date'))}",
                  f"- **Source class:** {clean(lead.get('source_class'))} (not automatically classified)",
                  f"- **Review:** {clean(lead.get('review_status'))}",
                  f"- **Summary:** {clean(lead.get('snippet'))}",
                  f"- **Original source:** {clean(lead.get('source_url'))}", ""]
    (out / "individual_source_briefs.md").write_text("\\n".join(lines), encoding="utf-8")

    def matches(pattern, lead):
        text = " ".join([str(lead.get("title") or ""), str(lead.get("snippet") or "")]).lower()
        return re.search(pattern, text, flags=re.I) is not None

    bangladesh = [x for x in leads if (x.get("region") or "").lower() == "bangladesh"]
    international = [x for x in leads if x not in bangladesh]
    rumour = [x for x in leads if x.get("claim_type") == "RUMOUR_WATCH"]
    communal = [x for x in leads if matches(r"communal|minority|sectarian|religious|ethnic|mob|lynch", x)]
    political = [x for x in leads if matches(r"politic|election|party|protest|rally|student|government|minister", x)]

    report = [
        f"# Legion-OSINT Preliminary Daily Discovery Report — {report_date}", "",
        "**Status: PRELIMINARY SOURCE-LEAD REPORT — NOT A VERIFIED INTELLIGENCE ASSESSMENT.**",
        "**Timezone:** Asia/Dhaka (UTC+6). Search-provider results only; platform coverage is incomplete.",
        f"Queries attempted: {summary['queries_attempted']}; succeeded: {summary['queries_succeeded']}; unique source leads stored: {len(leads)}.",
        "Source leads are not necessarily unique incidents. All claims require analyst review and independent corroboration.", "",
        "## 1. Executive Summary", "",
        f"Search returned {len(leads)} source leads from {summary['queries_succeeded']}/{summary['queries_attempted']} successful queries. "
        f"{len(bangladesh)} leads are tagged Bangladesh by query region; {len(rumour)} are rumour-watch leads. "
        "No incident is automatically verified by this workflow.", "",
        "## 2. Bangladesh Intelligence Report", "",
        f"Bangladesh-tagged source leads: {len(bangladesh)}.", ""
    ]
    for x in bangladesh:
        report.append(f"- **{clean(x.get('title'))}** — {clean(x.get('snippet'))} [Source]({x.get('source_url')}) (UNVERIFIED)")
    report += ["", "## 3. International Conflict and Security", "",
               f"Non-Bangladesh regional/global source leads: {len(international)}.", ""]
    for x in international:
        report.append(f"- **{clean(x.get('region'))}: {clean(x.get('title'))}** — {clean(x.get('snippet'))} [Source]({x.get('source_url')}) (UNVERIFIED)")
    report += ["", "## 4. Communal and Social Violence", "",
               f"{len(communal)} leads matched communal/social-violence screening terms. This is a keyword-based review queue, not a confirmed classification.", ""]
    for x in communal:
        report.append(f"- {clean(x.get('title'))} — [Source]({x.get('source_url')}) (UNVERIFIED; keyword-screened)")
    report += ["", "## 5. Political Developments", "",
               f"{len(political)} leads matched political-development screening terms. This is not an event determination.", ""]
    for x in political:
        report.append(f"- {clean(x.get('title'))} — [Source]({x.get('source_url')}) (UNVERIFIED; keyword-screened)")
    report += ["", "## 6. Misinformation and Information Operations", "",
               f"Rumour-watch discovery returned {len(rumour)} leads. Every item remains UNVERIFIED RUMOUR; inclusion is not endorsement.", ""]
    for x in rumour:
        report.append(f"- **UNVERIFIED RUMOUR:** {clean(x.get('title'))} — {clean(x.get('snippet'))} [Original source]({x.get('source_url')})")
    report += ["", "## 7. Source Lead Register", "",
               "| ID | Region | Claim type | Title | Publication date | Review | Source |",
               "|---|---|---|---|---|---|---|"]
    for x in leads:
        report.append(f"| {x.get('id')} | {clean(x.get('region'))} | {clean(x.get('claim_type'))} | {clean(x.get('title'))} | {clean(x.get('published_date'))} | UNREVIEWED | [Link]({x.get('source_url')}) |")
    report += ["", "## 8. Early-Warning Assessment", "",
               "No risk level or imminent-violence judgment is generated from search-result volume or rhetoric. Human assessment is required after verifying incident dates, locations, source independence, actors, context and corroboration.", "",
               "## 9. Source and Coverage Assessment", "",
               f"Search-focus queries: {summary['unofficial_focus_queries']} unofficial/public discovery; {summary['official_focus_queries']} official/institutional discovery. These are query-focus counts, not the actual source mix.", ""]
    for x in coverage:
        report.append(f"- {clean(x.get('region'))}: {x.get('status')} — {x.get('query_count')} queries; {x.get('result_count') or 0} provider results.")
    report += ["", "Provider indexing does not equal direct access to all Telegram, X, Facebook or YouTube content. Regional and language coverage is incomplete; publication dates may be missing or inaccurate.", "",
               "## 10. Overall Intelligence Judgment", "",
               "This run establishes only that the listed sources were surfaced by the configured search provider. It does not establish that reported events occurred, that the leads are independent, or that no other events occurred. Review and corroborate before drawing conclusions or publishing.", "",
               "## Publication safeguards", "",
               "- Do not convert a source lead into an incident without analyst review.",
               "- Distinguish incident date from publication date.",
               "- Do not count syndicated copies as independent corroboration.",
               "- Keep rumour claims explicitly labelled UNVERIFIED RUMOUR.",
               "- Do not infer identities, motives, casualties, coordinates or risk levels from incomplete snippets.",
               ""]
    (out / "preliminary_daily_report.md").write_text("\\n".join(report), encoding="utf-8")
    print(f"Saved {len(leads)} source leads and report files under {out}")
    if summary["queries_succeeded"] == 0:
        raise SystemExit("No search queries succeeded; inspect research_summary.json and provider configuration")

if __name__ == "__main__":
    main()
