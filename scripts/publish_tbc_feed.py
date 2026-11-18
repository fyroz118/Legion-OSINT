"""Publish a minimal public-source feed for the TBC read-only interface.

Only posts already visible on public Telegram preview pages are included.
No analyst decisions, incident drafts, private identifiers or credentials are published.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output"
DEST = ROOT / "docs" / "feed" / "latest.json"
MAX_POSTS = 1800
MAX_TEXT = 1800


def main():
    folders = sorted(p for p in OUTPUT.iterdir() if p.is_dir()) if OUTPUT.exists() else []
    if not folders:
        raise SystemExit("No collection output directory exists; refusing to publish an empty feed.")
    folder = folders[-1]
    posts_file = folder / "telegram_posts.csv"
    summary_file = folder / "collection_summary.json"
    if not posts_file.exists() or not summary_file.exists():
        raise SystemExit(f"Missing collection outputs in {folder}")

    import csv
    with posts_file.open("r", encoding="utf-8-sig", newline="") as handle:
        raw_posts = list(csv.DictReader(handle))
    with summary_file.open("r", encoding="utf-8") as handle:
        collection = json.load(handle)

    posts = []
    for row in raw_posts:
        username = (row.get("channel_username") or "").strip().lstrip("@")
        message_id = str(row.get("message_id") or "").strip()
        text = " ".join((row.get("text") or "").split())
        source_url = (row.get("source_url") or "").strip()
        if not username or not message_id or not text or not source_url.startswith("https://t.me/"):
            continue
        posts.append({
            "id": username + ":" + message_id,
            "channel_username": username,
            "published_at": row.get("published_at") or None,
            "collected_at": row.get("collected_at") or None,
            "text": text[:MAX_TEXT],
            "source_url": source_url,
            "language": row.get("language") or "unknown",
            "priority_region": row.get("priority_region") or "global",
            "source_class": row.get("source_class") or "unknown",
            "source_type": row.get("source_type") or "unknown",
            "source_affiliation": row.get("source_affiliation") or "unknown",
            "monitoring_weight": row.get("monitoring_weight") or "standard",
            "evidence_status": "UNVERIFIED"
        })
    posts.sort(key=lambda p: p.get("published_at") or "", reverse=True)
    posts = posts[:MAX_POSTS]

    diagnostics = collection.get("channel_diagnostics") or {}
    errors = collection.get("collection_errors") or []
    channels = collection.get("configured_channels") or []
    summary = {
        "report_date": collection.get("report_date"),
        "timezone": collection.get("timezone", "Asia/Dhaka"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "collection_method": collection.get("collection_method"),
        "configured_channels": len(channels),
        "channels_with_diagnostics": len(diagnostics),
        "posts_in_snapshot": len(posts),
        "collection_errors": len(errors),
        "channel_diagnostics": diagnostics,
        "limitations": collection.get("limitations") or [],
        "notice": "Public Telegram preview snapshot only. Posts are unverified leads; publication time is not incident time. This feed excludes analyst notes and incident decisions."
    }
    payload = {
        "schema_version": 1,
        "generated_at": summary["generated_at"],
        "summary": summary,
        "posts": posts
    }
    DEST.parent.mkdir(parents=True, exist_ok=True)
    temporary = DEST.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    temporary.replace(DEST)
    print(json.dumps({
        "feed": str(DEST.relative_to(ROOT)),
        "posts": len(posts),
        "configured_channels": len(channels),
        "collection_errors": len(errors),
        "generated_at": summary["generated_at"]
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
