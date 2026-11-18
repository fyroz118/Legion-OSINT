import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from scripts import publish_tbc_feed


class PublishTbcFeedTests(unittest.TestCase):
    def test_combines_public_telegram_and_rss_without_private_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            day = root / "output" / "2026-11-18"
            day.mkdir(parents=True)
            fields = ["channel_username", "message_id", "published_at", "collected_at", "text", "source_url", "language", "priority_region", "source_class", "source_type", "source_affiliation", "monitoring_weight", "publisher_name", "platform"]
            with (day / "telegram_posts.csv").open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                writer.writerow({"channel_username":"localreporter", "message_id":"77", "published_at":"2026-11-18T08:00:00Z", "collected_at":"2026-11-18T08:05:00Z", "text":"Public Telegram post", "source_url":"https://t.me/localreporter/77", "language":"bn", "priority_region":"bangladesh", "source_class":"unofficial", "source_type":"local_reporter", "source_affiliation":"unassessed", "monitoring_weight":"high", "publisher_name":"Local Reporter", "platform":"Telegram"})
            with (day / "news_articles.csv").open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                writer.writerow({"channel_username":"daily_star_rss", "message_id":"abc", "published_at":"2026-11-18T09:00:00+06:00", "collected_at":"2026-11-18T09:05:00Z", "text":"RSS headline and excerpt", "source_url":"https://www.thedailystar.net/story", "language":"en", "priority_region":"bangladesh", "source_class":"independent_media", "source_type":"public_rss_article", "source_affiliation":"newsroom", "monitoring_weight":"high", "publisher_name":"The Daily Star", "platform":"RSS/Atom"})
            (day / "collection_summary.json").write_text(json.dumps({"report_date":"2026-11-18", "configured_channels":["localreporter"], "channel_diagnostics":{"localreporter":{"stop_reason":"date_boundary"}}, "collection_errors":[], "limitations":["preview only"]}), encoding="utf-8")
            (day / "news_collection_summary.json").write_text(json.dumps({"configured_sources":["daily_star_rss"], "source_diagnostics":{"daily_star_rss":{"status":"ok"}}, "limitations":["RSS only"]}), encoding="utf-8")
            destination = root / "docs" / "feed" / "latest.json"
            with patch.object(publish_tbc_feed, "OUTPUT", root / "output"), patch.object(publish_tbc_feed, "DEST", destination):
                publish_tbc_feed.main()
            payload = json.loads(destination.read_text(encoding="utf-8"))
            self.assertEqual(len(payload["posts"]), 2)
            self.assertEqual(payload["schema_version"], 2)
            self.assertEqual({p["platform"] for p in payload["posts"]}, {"Telegram", "RSS/Atom"})
            self.assertTrue(all(p["evidence_status"] == "UNVERIFIED" for p in payload["posts"]))
            self.assertEqual(payload["summary"]["configured_rss_sources"], 1)
            self.assertNotIn("analyst_decisions", payload)

    def test_rejects_non_https_source_urls(self):
        row = {"channel_username":"bad", "message_id":"1", "text":"headline", "source_url":"http://example.org/a"}
        self.assertIsNone(publish_tbc_feed.normalize_row(row, "RSS/Atom"))


if __name__ == "__main__":
    unittest.main()
