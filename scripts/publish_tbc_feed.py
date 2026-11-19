"""Publish a bounded, read-only feed of public Telegram and RSS source leads.

The feed contains public source material only. Analyst notes, decisions, incident
drafts, private identifiers and credentials are never published.
"""
import csv
import json
from datetime import datetime, timezone, date
from zoneinfo import ZoneInfo
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output"
DEST = ROOT / "docs" / "feed" / "latest.json"
ARCHIVE_DIR = ROOT / "docs" / "feed" / "archive"
MAX_POSTS = 1800
MAX_ARCHIVE_POSTS = 5000  # Bound the public feed; collection workflow publishes from main only.
MAX_TEXT = 3000


def read_csv(path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def normalize_row(row, platform):
    username = (row.get("channel_username") or row.get("source_id") or "").strip().lstrip("@")
    message_id = str(row.get("message_id") or row.get("id") or "").strip()
    text = " ".join((row.get("text") or "").split())
    source_url = (row.get("source_url") or row.get("url") or "").strip()
    if not username or not message_id or not text or not source_url.startswith("https://"):
        return None
    source_platform = row.get("platform") or platform
    publisher_name = row.get("publisher_name") or username
    display_source = ("RSS: " + publisher_name) if source_platform == "RSS/Atom" else username
    return {
        "id": username + ":" + message_id,
        "channel_username": display_source,
        "publisher_name": publisher_name,
        "platform": source_platform,
        "published_at": row.get("published_at") or None,
        "collected_at": row.get("collected_at") or None,
        "text": text[:MAX_TEXT],
        "source_url": source_url,
        "language": row.get("language") or "unknown",
        "priority_region": row.get("priority_region") or "global",
        "source_class": row.get("source_class") or "unknown",
        "source_type": row.get("source_type") or platform.lower(),
        "source_affiliation": row.get("source_affiliation") or "unknown",
        "monitoring_weight": row.get("monitoring_weight") or "standard",
        "evidence_status": "UNVERIFIED",
    }


def main():
    folders = sorted(p for p in OUTPUT.iterdir() if p.is_dir()) if OUTPUT.exists() else []
    if not folders:
        raise SystemExit("No collection output directory exists; refusing to publish an empty feed.")
    folder = folders[-1]
    telegram_file = folder / "telegram_posts.csv"
    telegram_summary_file = folder / "collection_summary.json"
    if not telegram_file.exists() or not telegram_summary_file.exists():
        raise SystemExit(f"Missing Telegram collection outputs in {folder}")
    telegram_rows = read_csv(telegram_file)
    with telegram_summary_file.open("r", encoding="utf-8") as handle:
        telegram_summary = json.load(handle)
    rss_rows = read_csv(folder / "news_articles.csv")
    rss_summary = {}
    if (folder / "news_collection_summary.json").exists():
        with (folder / "news_collection_summary.json").open("r", encoding="utf-8") as handle:
            rss_summary = json.load(handle)

    posts = []
    for row in telegram_rows:
        item = normalize_row(row, "Telegram")
        if item:
            posts.append(item)
    for row in rss_rows:
        item = normalize_row(row, "RSS/Atom")
        if item:
            posts.append(item)
    unique = {}
    for post in posts:
        unique[post["id"]] = post
    posts = sorted(unique.values(), key=lambda p: p.get("published_at") or "", reverse=True)[:MAX_POSTS]

    diagnostics = telegram_summary.get("channel_diagnostics") or {}
    errors = telegram_summary.get("collection_errors") or []
    channels = telegram_summary.get("configured_channels") or []
    rss_diagnostics = rss_summary.get("source_diagnostics") or {}
    summary = {
        "report_date": telegram_summary.get("report_date"),
        "timezone": telegram_summary.get("timezone", "Asia/Dhaka"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "collection_methods": [telegram_summary.get("collection_method"), rss_summary.get("collection_method")],
        "configured_telegram_channels": len(channels),
        "configured_channels": len(channels),  # backward-compatible TBC status/coverage field
        "channels_with_diagnostics": len(diagnostics),
        "telegram_channels_with_diagnostics": len(diagnostics),
        "telegram_posts_in_snapshot": sum(1 for p in posts if p["platform"] == "Telegram"),
        "configured_rss_sources": len(rss_summary.get("configured_sources") or []),
        "rss_sources_with_diagnostics": len(rss_diagnostics),
        "rss_articles_in_snapshot": sum(1 for p in posts if p["platform"] == "RSS/Atom"),
        "posts_in_snapshot": len(posts),
        "telegram_collection_errors": len(errors),
        "collection_errors": len(errors),  # backward-compatible TBC status/coverage field
        "rss_source_errors": sum(1 for d in rss_diagnostics.values() if d.get("status") == "error"),
        "channel_diagnostics": diagnostics,
        "rss_source_diagnostics": rss_diagnostics,
        "limitations": (telegram_summary.get("limitations") or []) + (rss_summary.get("limitations") or []),
        "notice": "Public Telegram preview posts and public RSS/Atom headlines/excerpts only. All items are unverified source leads; publication time is not incident time. Repeated coverage is not independent corroboration. This feed excludes analyst notes and incident decisions.",
    }
    payload = {"schema_version": 2, "generated_at": summary["generated_at"], "summary": summary, "posts": posts}
    DEST.parent.mkdir(parents=True, exist_ok=True)
    temporary = DEST.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    temporary.replace(DEST)

    # Maintain a per-day archive by merging each scheduled collection run.
    # This preserves posts collected earlier in the same day instead of
    # replacing the archive with only the newest two-hour collection window.
    report_date = str(summary.get("report_date") or "")
    timezone_name = str(summary.get("timezone") or "Asia/Dhaka")
    try:
        date.fromisoformat(report_date)
        archive_path = ARCHIVE_DIR / (report_date + ".json")
        archived_posts = {}
        if archive_path.exists():
            try:
                previous = json.loads(archive_path.read_text(encoding="utf-8"))
                for item in previous.get("posts", []):
                    if item.get("id"):
                        archived_posts[item["id"]] = item
            except (OSError, ValueError, TypeError):
                print("Warning: previous daily archive could not be read; rebuilding from current collection.")
        try:
            local_tz = ZoneInfo(timezone_name)
        except Exception:
            local_tz = ZoneInfo("Asia/Dhaka")
        for item in posts:
            stamp = str(item.get("published_at") or "").strip()
            if not stamp:
                continue
            try:
                parsed_stamp = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
                if parsed_stamp.tzinfo is None:
                    parsed_stamp = parsed_stamp.replace(tzinfo=timezone.utc)
                item_day = parsed_stamp.astimezone(local_tz).date().isoformat()
            except (ValueError, TypeError, OverflowError):
                continue
            if item_day == report_date:
                archived_posts[item["id"]] = item
        day_posts = sorted(archived_posts.values(), key=lambda item: item.get("published_at") or "")[-MAX_ARCHIVE_POSTS:]
        archive_summary = dict(summary)
        archive_summary.update({
            "archive_date": report_date,
            "archive_timezone": timezone_name,
            "archive_posts": len(day_posts),
            "archive_notice": "Daily rolling archive merged from scheduled public-source collection runs. Coverage is bounded by public preview/RSS access and collector limits; this is not a complete record of all posts or news."
        })
        archive_payload = {"schema_version": 1, "generated_at": summary["generated_at"], "summary": archive_summary, "posts": day_posts}
        ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
        archive_tmp = archive_path.with_suffix(".tmp")
        archive_tmp.write_text(json.dumps(archive_payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        archive_tmp.replace(archive_path)

        # Publish small page-sized files for chatbots with response-size/time limits.
        # TBC fetches only one page (20 records) instead of downloading the full multi-MB archive.
        page_dir = ARCHIVE_DIR / report_date
        page_dir.mkdir(parents=True, exist_ok=True)
        page_size = 20
        total_pages = max(1, (len(day_posts) + page_size - 1) // page_size)
        for page_number in range(1, total_pages + 1):
            page_posts = day_posts[(page_number - 1) * page_size:page_number * page_size]
            page_summary = dict(archive_summary)
            page_summary.update({
                "page": page_number,
                "total_pages": total_pages,
                "page_size": page_size,
                "page_records": len(page_posts),
                "total_records": len(day_posts)
            })
            page_payload = {
                "schema_version": 1,
                "generated_at": summary["generated_at"],
                "summary": page_summary,
                "posts": page_posts
            }
            page_path = page_dir / ("page-" + str(page_number) + ".json")
            page_tmp = page_path.with_suffix(".tmp")
            page_tmp.write_text(json.dumps(page_payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
            page_tmp.replace(page_path)

        # Build a compact, deterministic daily source-activity summary for TBC.
        # Topic labels are keyword indicators, not verified incident classifications.
        topic_terms = {
            "Politics and governance": ["election", "government", "parliament", "minister", "political", "party", "court", "policy", "cabinet", "vote"],
            "Conflict and security": ["attack", "armed", "military", "soldier", "clash", "explosion", "bomb", "security", "killed", "airstrike", "war"],
            "Protests and labour unrest": ["protest", "demonstration", "strike", "rally", "march", "workers", "student movement", "shutdown", "hartal"],
            "Communal and social violence": ["communal", "religious violence", "mob", "lynching", "riot", "sectarian", "arson", "vandalism"],
            "Public health": ["outbreak", "disease", "health ministry", "hospital", "epidemic", "infection", "cholera", "dengue", "measles", "vaccination"],
            "Disasters and environment": ["flood", "cyclone", "earthquake", "landslide", "fire", "storm", "heatwave", "drought", "pollution"],
            "Economy and essential services": ["inflation", "price", "economy", "fuel", "power", "electricity", "blackout", "bank", "currency", "trade"]
        }
        topic_matches = {label: [] for label in topic_terms}
        region_counts = {}
        source_class_counts = {}
        platform_counts = {"Telegram": 0, "RSS/Atom": 0}
        for item in day_posts:
            body = str(item.get("text") or "").lower()
            platform = str(item.get("platform") or "Unknown")
            region = str(item.get("priority_region") or "global")
            source_class = str(item.get("source_class") or "unknown")
            platform_counts[platform] = platform_counts.get(platform, 0) + 1
            region_counts[region] = region_counts.get(region, 0) + 1
            source_class_counts[source_class] = source_class_counts.get(source_class, 0) + 1
            for label, terms in topic_terms.items():
                if any(term in body for term in terms):
                    topic_matches[label].append(item)
        topic_indicators = []
        for label, matches in topic_matches.items():
            if matches:
                topic_indicators.append({
                    "topic": label,
                    "matching_source_posts": len(matches),
                    "representative_posts": [{
                        "publisher_name": p.get("publisher_name"),
                        "channel_username": p.get("channel_username"),
                        "platform": p.get("platform"),
                        "published_at": p.get("published_at"),
                        "priority_region": p.get("priority_region"),
                        "source_class": p.get("source_class"),
                        "text": str(p.get("text") or "")[:500],
                        "source_url": p.get("source_url")
                    } for p in matches[:3]]
                })
        topic_indicators.sort(key=lambda x: x["matching_source_posts"], reverse=True)
        summary_posts = sorted(day_posts, key=lambda p: (str(p.get("monitoring_weight", "")).lower() == "high", str(p.get("published_at") or "")), reverse=True)[:12]
        daily_summary = {
            "schema_version": 1,
            "generated_at": summary["generated_at"],
            "report_date": report_date,
            "timezone": timezone_name,
            "total_source_posts": len(day_posts),
            "platform_counts": platform_counts,
            "region_counts": region_counts,
            "source_class_counts": source_class_counts,
            "topic_indicators": topic_indicators,
            "representative_posts": [{
                "publisher_name": p.get("publisher_name"),
                "channel_username": p.get("channel_username"),
                "platform": p.get("platform"),
                "published_at": p.get("published_at"),
                "priority_region": p.get("priority_region"),
                "source_class": p.get("source_class"),
                "text": str(p.get("text") or "")[:500],
                "source_url": p.get("source_url")
            } for p in summary_posts],
            "notice": "Automated keyword-based source-activity summary, not an AI-verified event synthesis. Topic matches can be false positives or miss relevant posts. Posts are unverified; repeated posts are not independent corroboration; publication time is not incident time; empty categories do not mean no events occurred."
        }
        summary_path = page_dir / "summary.json"
        summary_tmp = summary_path.with_suffix(".tmp")
        summary_tmp.write_text(json.dumps(daily_summary, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        summary_tmp.replace(summary_path)

        # Build a fuller source-driven daily intelligence report for the TBC /summary command.
        # This is structured OSINT triage, not LLM-generated event verification or causal attribution.
        region_labels = {
            "bangladesh": "Bangladesh",
            "south asia": "South Asia",
            "myanmar": "Myanmar",
            "mena": "MENA",
            "europe": "Europe and Ukraine",
            "sub-saharan africa": "Sub-Saharan Africa",
            "americas": "Americas",
            "east/southeast asia": "East and Southeast Asia",
            "global": "Global / unassigned"
        }
        region_posts = {}
        for item in day_posts:
            region_key = str(item.get("priority_region") or "global").strip().lower()
            region_posts.setdefault(region_key, []).append(item)
        def report_post(item):
            return {
                "id": item.get("id"),
                "publisher_name": item.get("publisher_name"),
                "channel_username": item.get("channel_username"),
                "platform": item.get("platform"),
                "published_at": item.get("published_at"),
                "priority_region": item.get("priority_region"),
                "source_class": item.get("source_class"),
                "source_affiliation": item.get("source_affiliation"),
                "monitoring_weight": item.get("monitoring_weight"),
                "evidence_status": "UNVERIFIED",
                "text": str(item.get("text") or "")[:900],
                "source_url": item.get("source_url")
            }
        # Broad coverage: retain up to 100 distinct source records, balancing regions before filling by recency.
        selected_report_posts = []
        seen_ids = set()
        region_order = sorted(region_posts, key=lambda key: (key != "bangladesh", -len(region_posts[key]), key))
        for index in range(20):
            for region_key in region_order:
                candidates = region_posts.get(region_key, [])
                if index < len(candidates):
                    item = candidates[index]
                    if item.get("id") not in seen_ids and len(selected_report_posts) < 100:
                        selected_report_posts.append(item)
                        seen_ids.add(item.get("id"))
        if len(selected_report_posts) < 100:
            for item in sorted(day_posts, key=lambda p: str(p.get("published_at") or ""), reverse=True):
                if item.get("id") not in seen_ids:
                    selected_report_posts.append(item)
                    seen_ids.add(item.get("id"))
                if len(selected_report_posts) >= 100:
                    break
        # Keyword buckets are discovery aids only. A post can match more than one bucket.
        report_buckets = {
            "Political and governance developments": ["government", "minister", "election", "parliament", "party", "opposition", "court", "president", "prime minister", "political"],
            "Armed conflict and security": ["attack", "airstrike", "drone", "military", "army", "soldier", "clash", "explosion", "bomb", "militant", "war", "missile"],
            "Protests, labour and civil unrest": ["protest", "demonstration", "strike", "workers", "labour", "labor", "shutdown", "hartal", "blockade", "riot"],
            "Communal and identity-related violence": ["communal", "sectarian", "religious violence", "mosque", "temple", "church", "lynching", "mob attack", "hate crime"],
            "Public health and humanitarian": ["outbreak", "epidemic", "cholera", "dengue", "hospital", "displacement", "refugee", "famine", "malnutrition"],
            "Infrastructure, economy and essential services": ["power plant", "electricity", "blackout", "fuel", "bank", "factory", "port", "railway", "airport", "shipping", "inflation"],
            "Disasters and environment": ["flood", "cyclone", "earthquake", "landslide", "wildfire", "drought", "storm", "heatwave"]
        }
        bucket_results = []
        for label, terms in report_buckets.items():
            matches = []
            for item in day_posts:
                body = str(item.get("text") or "").lower()
                if any(term in body for term in terms):
                    matches.append(item)
            if matches:
                bucket_results.append({
                    "section": label,
                    "matching_source_posts": len(matches),
                    "source_records": [report_post(p) for p in sorted(matches, key=lambda p: str(p.get("published_at") or ""), reverse=True)[:15]]
                })
        bucket_results.sort(key=lambda x: x["matching_source_posts"], reverse=True)
        region_sections = []
        for region_key in region_order:
            records = region_posts[region_key]
            region_sections.append({
                "region": region_labels.get(region_key, region_key.replace("_", " ").title()),
                "source_post_count": len(records),
                "source_records": [report_post(p) for p in sorted(records, key=lambda p: str(p.get("published_at") or ""), reverse=True)[:20]]
            })
        incident_terms = ["killed", "dead", "injured", "wounded", "arrest", "detained", "arson", "burn", "fire", "bomb", "explosion", "attack", "clash", "abduct", "displaced", "blockade"]
        incident_candidates = []
        for item in sorted(day_posts, key=lambda p: str(p.get("published_at") or ""), reverse=True):
            body = str(item.get("text") or "").lower()
            if any(term in body for term in incident_terms):
                incident_candidates.append(report_post(item))
        intelligence_report = {
            "schema_version": 1,
            "report_date": report_date,
            "timezone": timezone_name,
            "generated_at": summary["generated_at"],
            "title": "Legion-OSINT Daily Global Conflict and Communal-Risk Early-Warning Report",
            "classification": "Open-Source Intelligence — unverified source-lead assessment",
            "executive_assessment": {
                "source_posts_in_daily_archive": len(day_posts),
                "telegram_posts": platform_counts.get("Telegram", 0),
                "rss_articles": platform_counts.get("RSS/Atom", 0),
                "regions_represented": len(region_posts),
                "source_classes": source_class_counts,
                "key_caveat": "This automated report organizes collected public-source material. It does not independently verify incidents, establish perpetrator attribution, determine motive, or synthesize a reliable event chronology."
            },
            "report_sections": [
                {"heading": "1. Executive assessment and collection picture", "text": "Daily source-volume and coverage indicators are descriptive counts of collected posts/articles, not incident counts or measures of conflict intensity."},
                {"heading": "2. Bangladesh political-security and communal-risk watch", "text": "Bangladesh records are prioritised where present. Political violence, labour unrest, ordinary crime and religiously motivated targeting must be assessed separately; affiliation or motive is not inferred from keywords.", "source_records": [report_post(p) for p in sorted(region_posts.get("bangladesh", []), key=lambda p: str(p.get("published_at") or ""), reverse=True)[:40]]},
                {"heading": "3. Regional and international conflict monitoring", "text": "Regional source leads are grouped below. Reposts and syndicated reports are not independent corroboration.", "regions": region_sections},
                {"heading": "4. Communal violence and hate-crime tracker", "text": "No post is classified as a verified hate crime by keyword matching. Review the original source and establish protected-group targeting, motive, location and incident date before classification.", "source_records": [report_post(p) for p in sorted(day_posts, key=lambda p: str(p.get("published_at") or ""), reverse=True) if any(term in str(p.get("text") or "").lower() for term in ["communal", "sectarian", "religious violence", "mosque", "temple", "church", "lynching", "hate crime"])][:30]},
                {"heading": "5. Social-media OSINT and emerging narratives", "text": "Telegram records are public-preview source leads. Treat eyewitness and unofficial posts as leads; verify original upload, geolocation, chronology, media provenance and independent corroboration.", "source_records": [report_post(p) for p in selected_report_posts if p.get("platform") == "Telegram"][:50]},
                {"heading": "6. Topic and narrative indicators", "text": "Buckets below are overlapping keyword matches, not unique events, verified incidents, or evidence of coordination.", "topic_buckets": bucket_results},
                {"heading": "7. Incident register — candidate leads", "text": "These are source-post candidates, not deduplicated incidents. Multiple posts may describe one event; one post may contain several claims. Verification status remains UNVERIFIED.", "candidate_records": incident_candidates[:60]},
                {"heading": "8. Early-warning indicators and risk movement", "text": "Automated collection cannot assign defensible risk ratings or forecast violence. Analysts should assess changes against prior periods using corroborated incidents, actor capability, intent indicators, target selection and protective factors.", "watch_indicators": ["New verified fatalities or mass-casualty claims", "Repeated attacks on transport, health, energy or communications infrastructure", "Threats or mobilisation linked to identifiable targets", "Cross-district spread supported by independently sourced incidents", "Retaliatory mobilisation, communal targeting or displacement", "Arrests, curfews, emergency deployments and restrictions with verified scope"]},
                {"heading": "9. Sources, bias and coverage limitations", "text": "Source class and affiliation are descriptive metadata and may be incomplete. Public Telegram previews and RSS/Atom feeds are bounded; absence of a post is not evidence of no event. Publication time is not incident time; repost volume is not corroboration."},
                {"heading": "10. Overall intelligence judgement", "text": "This is a structured collection digest for analyst review, not an automated strategic judgement. A human analyst must reconcile conflicting claims, deduplicate posts into incidents, verify dates/locations/casualties, assess attribution and motive, and document confidence with reasons."}
            ],
            "source_records_selected": len(selected_report_posts),
            "source_records_available": len(day_posts),
            "minimum_target_met": len(day_posts) >= 50,
            "source_records": [report_post(p) for p in selected_report_posts],
            "notice": "UNVERIFIED SOURCE LEADS. This report is generated deterministically from collected public posts/articles. It is not an AI-generated or independently verified event synthesis. Keyword matches can be false positives or miss events. No inference of guilt, central direction, religious motive or imminent violence is made. Check original sources before reporting."
        }
        intelligence_path = page_dir / "intelligence_report.json"
        intelligence_tmp = intelligence_path.with_suffix(".tmp")
        intelligence_tmp.write_text(json.dumps(intelligence_report, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        intelligence_tmp.replace(intelligence_path)
    except ValueError:
        raise SystemExit("Invalid report_date; refusing to publish a daily archive.")

    print(json.dumps({"feed": str(DEST), "posts": len(posts), "daily_archive": str(archive_path), "daily_archive_posts": len(day_posts), "telegram_posts": summary["telegram_posts_in_snapshot"], "rss_articles": summary["rss_articles_in_snapshot"], "telegram_errors": len(errors), "rss_errors": summary["rss_source_errors"], "generated_at": summary["generated_at"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
