"""Publish a bounded, read-only feed of public Telegram and RSS source leads.

The feed contains public source material only. Analyst notes, decisions, incident
drafts, private identifiers and credentials are never published.
"""
import csv
import json
from datetime import datetime, timezone
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
    except ValueError:
        raise SystemExit("Invalid report_date; refusing to publish a daily archive.")

    print(json.dumps({"feed": str(DEST), "posts": len(posts), "daily_archive": str(archive_path), "daily_archive_posts": len(day_posts), "telegram_posts": summary["telegram_posts_in_snapshot"], "rss_articles": summary["rss_articles_in_snapshot"], "telegram_errors": len(errors), "rss_errors": summary["rss_source_errors"], "generated_at": summary["generated_at"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
