#!/usr/bin/env python3
"""Collect public RSS/Atom headlines as attributed, unverified news leads.

Uses only standard-library XML parsing and HTTP. It does not scrape article
bodies, bypass access controls, or infer that an article describes a verified
incident. Output is a bounded 72-hour window for the TBC public-source feed.
"""
import csv
import hashlib
import html
import json
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "news_sources.json"
OUT = ROOT / "output"
TZ = ZoneInfo("Asia/Dhaka")
USER_AGENT = "Legion-OSINT/1.0 (+public RSS headline collection; see repository README)"
MAX_FEED_BYTES = 4_000_000
MAX_ITEMS_PER_SOURCE = 60
LOOKBACK_HOURS = 72


class TextOnly(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
    def handle_data(self, data):
        if data and data.strip():
            self.parts.append(data.strip())


def local_name(tag):
    return tag.rsplit("}", 1)[-1].lower()


def child_text(node, names):
    wanted = set(names)
    for child in list(node):
        if local_name(child.tag) in wanted:
            if local_name(child.tag) == "link":
                href = child.attrib.get("href")
                if href:
                    return href.strip()
            value = "".join(child.itertext()).strip()
            if value:
                return value
    return ""


def clean_text(value, limit=3000):
    parser = TextOnly()
    try:
        parser.feed(html.unescape(value or ""))
        text = " ".join(parser.parts)
    except Exception:
        text = re.sub(r"<[^>]+>", " ", html.unescape(value or ""))
    return re.sub(r"\s+", " ", text).strip()[:limit]


def parse_datetime(value):
    if not value:
        return None
    value = value.strip()
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed = parsedate_to_datetime(value)
        except (TypeError, ValueError, OverflowError):
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def parse_feed(xml_bytes):
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        # Some publisher feeds contain stray control characters or bare ampersands.
        repaired = xml_bytes.decode("utf-8-sig", "replace")
        repaired = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", repaired)
        repaired = re.sub(r"&(?!#(?:x[0-9a-fA-F]+|[0-9]+);|(?:amp|lt|gt|quot|apos);)", "&amp;", repaired)
        root = ET.fromstring(repaired)
    entries = [node for node in root.iter() if local_name(node.tag) in ("item", "entry")]
    results = []
    for entry in entries:
        title = child_text(entry, ("title",))
        link = child_text(entry, ("link",))
        if not link:
            guid_value = child_text(entry, ("guid", "id"))
            if guid_value.startswith(("https://", "http://")):
                link = guid_value
        summary = child_text(entry, ("description", "summary", "encoded", "content"))
        published = child_text(entry, ("pubdate", "published", "updated", "date"))
        guid = child_text(entry, ("guid", "id"))
        stamp = parse_datetime(published)
        if not title or not link or not link.startswith(("https://", "http://")):
            continue
        results.append({
            "title": clean_text(title, 500),
            "summary": clean_text(summary, 2500),
            "url": link.strip(),
            "guid": guid.strip()[:1000],
            "published_utc": stamp.isoformat() if stamp else "",
            "_published_dt": stamp,
        })
    return results


def fetch_feed(url):
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("feed_url_must_be_https")
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml;q=0.9, */*;q=0.5"})
    with urlopen(request, timeout=20) as response:
        payload = response.read(MAX_FEED_BYTES + 1)
    if len(payload) > MAX_FEED_BYTES:
        raise ValueError("feed_exceeds_size_limit")
    return parse_feed(payload)


def stable_id(source_id, item):
    identity = item.get("guid") or item.get("url")
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:20]
    return source_id + ":" + digest


def collect_source(source, now):
    diagnostic = {"status": "ok", "items_parsed": 0, "items_in_window": 0, "items_without_timestamp": 0, "latest_published_at": None, "error": None}
    try:
        items = fetch_feed(source["feed_url"])
        diagnostic["items_parsed"] = len(items)
        cutoff = now - timedelta(hours=LOOKBACK_HOURS)
        rows = []
        seen = set()
        for item in items[:MAX_ITEMS_PER_SOURCE]:
            published = item.pop("_published_dt")
            if not published:
                diagnostic["items_without_timestamp"] += 1
                continue
            if published < cutoff or published > now + timedelta(hours=6):
                continue
            item_id = stable_id(source["source_id"], item)
            if item_id in seen:
                continue
            seen.add(item_id)
            body = item["title"]
            if item["summary"]:
                body += " — " + item["summary"]
            rows.append({
                "channel_username": source["source_id"],
                "channel_id": "",
                "message_id": item_id.split(":", 1)[1],
                "published_at": published.astimezone(TZ).isoformat(),
                "collected_at": now.isoformat(),
                "text": body[:3000],
                "source_url": item["url"],
                "language": source.get("language", "unknown"),
                "priority_region": source.get("priority_region", "global"),
                "source_class": source.get("source_class", "unknown"),
                "source_type": "public_rss_article",
                "source_affiliation": source.get("source_affiliation", "unassessed"),
                "monitoring_weight": source.get("monitoring_weight", "standard"),
                "publisher_name": source.get("publisher_name", source["source_id"]),
                "platform": "RSS/Atom",
                "article_title": item["title"],
                "article_summary": item["summary"],
                "feed_url": source["feed_url"],
                "guid": item["guid"],
                "evidence_status": "UNVERIFIED",
            })
        diagnostic["items_in_window"] = len(rows)
        if rows:
            diagnostic["latest_published_at"] = max(r["published_at"] for r in rows)
        return rows, diagnostic
    except Exception as exc:
        diagnostic["status"] = "error"
        diagnostic["error"] = f"{type(exc).__name__}: {str(exc)[:220]}"
        return [], diagnostic


def main():
    now = datetime.now(timezone.utc)
    report_day = now.astimezone(TZ).date().isoformat()
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    sources = [s for s in config.get("sources", []) if s.get("enabled", True)]
    rows, diagnostics = [], {}
    for source in sources:
        found, diagnostic = collect_source(source, now)
        rows.extend(found)
        diagnostics[source["source_id"]] = diagnostic
        print(f"{source['source_id']}: {len(found)} recent articles; {diagnostic['status']}", flush=True)
        time.sleep(0.25)
    rows.sort(key=lambda row: row.get("published_at") or "", reverse=True)
    out = OUT / report_day
    out.mkdir(parents=True, exist_ok=True)
    fields = ["channel_username", "channel_id", "message_id", "published_at", "collected_at", "text", "source_url", "language", "priority_region", "source_class", "source_type", "source_affiliation", "monitoring_weight", "publisher_name", "platform", "article_title", "article_summary", "feed_url", "guid", "evidence_status"]
    with (out / "news_articles.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    summary = {
        "report_date": report_day,
        "timezone": "Asia/Dhaka",
        "collection_method": "public RSS/Atom headline and excerpt feeds; no article-body scraping",
        "lookback_hours": LOOKBACK_HOURS,
        "configured_sources": [s["source_id"] for s in sources],
        "articles_in_window": len(rows),
        "source_diagnostics": diagnostics,
        "limitations": [
            "RSS availability and update frequency vary by publisher; errors are shown per source.",
            "Only public feed headlines and excerpts are collected; full article content is not mirrored.",
            "Articles are unverified source leads; publication time is not incident time.",
            "Multiple articles may describe the same event and are not automatically independent corroboration.",
            "No social-media platform beyond the separately configured public Telegram preview collector is searched.",
        ],
    }
    (out / "news_collection_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"date": report_day, "sources": len(sources), "articles": len(rows), "source_errors": sum(1 for d in diagnostics.values() if d["status"] == "error")}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
