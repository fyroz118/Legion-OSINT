import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import publish_tbc_feed


class PublishTbcFeedTests(unittest.TestCase):
    def test_publishes_only_public_post_fields_and_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "output"
            day = output / "2026-11-18"
            day.mkdir(parents=True)
            with (day / "telegram_posts.csv").open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=[
                    "channel_username", "message_id", "published_at", "collected_at",
                    "text", "source_url", "language", "priority_region", "source_class",
                    "source_type", "source_affiliation", "monitoring_weight"
                ])
                writer.writeheader()
                writer.writerow({
                    "channel_username": "localreporter", "message_id": "77",
                    "published_at": "2026-11-18T08:00:00Z",
                    "collected_at": "2026-11-18T08:05:00Z",
                    "text": "  Public   post text  ",
                    "source_url": "https://t.me/localreporter/77",
                    "language": "bn", "priority_region": "Bangladesh",
                    "source_class": "unofficial", "source_type": "local_reporter",
                    "source_affiliation": "independent", "monitoring_weight": "high"
                })
                writer.writerow({
                    "channel_username": "badsource", "message_id": "88",
                    "text": "must be excluded", "source_url": "https://example.com/not-telegram"
                })
            (day / "collection_summary.json").write_text(json.dumps({
                "report_date": "2026-11-18",
                "configured_channels": ["localreporter"],
                "channel_diagnostics": {"localreporter": {"stop_reason": "date_boundary"}},
                "collection_errors": [],
                "limitations": ["preview only"]
            }), encoding="utf-8")
            destination = root / "docs" / "feed" / "latest.json"
            with patch.object(publish_tbc_feed, "OUTPUT", output), patch.object(publish_tbc_feed, "DEST", destination):
                publish_tbc_feed.main()
            payload = json.loads(destination.read_text(encoding="utf-8"))
            self.assertEqual(len(payload["posts"]), 1)
            post = payload["posts"][0]
            self.assertEqual(post["id"], "localreporter:77")
            self.assertEqual(post["text"], "Public post text")
            self.assertEqual(post["evidence_status"], "UNVERIFIED")
            self.assertNotIn("analyst_decisions", payload)
            self.assertEqual(payload["summary"]["configured_channels"], 1)


if __name__ == "__main__":
    unittest.main()
