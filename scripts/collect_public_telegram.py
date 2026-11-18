"""Scheduled, unauthenticated public Telegram preview collector.

Collects only configured public channels; posts remain unverified source leads.
"""
import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.run_telegram_gemini import collect_channel

TZ = ZoneInfo("Asia/Dhaka")

def main():
    day = datetime.now(TZ).date().isoformat()
    cap = max(1, min(int(os.getenv("COLLECT_LIMIT_PER_CHANNEL", "100")), 300))
    config = json.loads((ROOT / "config/channels.json").read_text(encoding="utf-8"))
    channels = [c for c in config.get("channels", [])
                if c.get("username") and c.get("enabled", True)
                and not c["username"].startswith("REPLACE_")]
    out = ROOT / "output" / day
    out.mkdir(parents=True, exist_ok=True)
    rows, errors, diagnostics, pages = [], [], {}, {}
    for channel in channels:
        found, failed, page_count, diagnostic = collect_channel(channel, day, cap)
        rows.extend(found)
        errors.extend(failed)
        diagnostics[channel["username"]] = diagnostic
        pages[channel["username"]] = page_count
        print(f"@{channel['username']}: {len(found)} posts for {day}; pages={page_count}; stop={diagnostic['stop_reason']}", flush=True)
    fields = ["channel_username","channel_id","message_id","published_at","collected_at","text",
              "source_url","language","priority_region","source_class","source_type",
              "source_affiliation","monitoring_weight","publisher_name","platform"]
    with (out / "telegram_posts.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    summary = {
        "report_date": day, "timezone": "Asia/Dhaka",
        "collection_method": "unauthenticated configured public Telegram preview pages",
        "configured_channels": [c["username"] for c in channels],
        "posts_for_date": len(rows), "pages_fetched_per_channel": pages,
        "channel_diagnostics": diagnostics, "collection_errors": errors,
        "limitations": ["No Telegram global search or private groups",
                        "No X, Facebook, YouTube or general news-site collection",
                        "Posts are unverified leads; publication date is not necessarily incident date"]
    }
    (out / "collection_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"date": day, "channels": len(channels), "posts": len(rows), "errors": len(errors)}, ensure_ascii=False), flush=True)

if __name__ == "__main__":
    main()
