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
                writer.writerow({"channel_username":"localreporter", "message_id":"77", "published_at":"2026-11-18T08:00:00Z", "collected_at":"2026-11-18T08:05:00Z", "text":"Armed attack reported in Gazipur; three people were injured.", "source_url":"https://t.me/localreporter/77", "language":"bn", "priority_region":"bangladesh", "source_class":"unofficial", "source_type":"local_reporter", "source_affiliation":"unassessed", "monitoring_weight":"high", "publisher_name":"Local Reporter", "platform":"Telegram"})
            with (day / "news_articles.csv").open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                writer.writerow({"channel_username":"daily_star_rss", "message_id":"abc", "published_at":"2026-11-18T09:00:00+06:00", "collected_at":"2026-11-18T09:05:00Z", "text":"Actress wears a bridal dress in a fashion photo shoot.", "source_url":"https://www.thedailystar.net/story", "language":"en", "priority_region":"bangladesh", "source_class":"independent_media", "source_type":"public_rss_article", "source_affiliation":"newsroom", "monitoring_weight":"high", "publisher_name":"The Daily Star", "platform":"RSS/Atom"})
            (day / "collection_summary.json").write_text(json.dumps({"report_date":"2026-11-18", "configured_channels":["localreporter"], "channel_diagnostics":{"localreporter":{"stop_reason":"date_boundary"}}, "collection_errors":[], "limitations":["preview only"]}), encoding="utf-8")
            (day / "news_collection_summary.json").write_text(json.dumps({"configured_sources":["daily_star_rss"], "source_diagnostics":{"daily_star_rss":{"status":"ok"}}, "limitations":["RSS only"]}), encoding="utf-8")
            destination = root / "docs" / "feed" / "latest.json"
            archive_dir = root / "docs" / "feed" / "archive"
            with patch.object(publish_tbc_feed, "OUTPUT", root / "output"), patch.object(publish_tbc_feed, "DEST", destination), patch.object(publish_tbc_feed, "ARCHIVE_DIR", archive_dir):
                publish_tbc_feed.main()
            payload = json.loads(destination.read_text(encoding="utf-8"))
            self.assertEqual(len(payload["posts"]), 2)
            self.assertEqual(payload["schema_version"], 2)
            self.assertEqual({p["platform"] for p in payload["posts"]}, {"Telegram", "RSS/Atom"})
            rss_post = next(p for p in payload["posts"] if p["platform"] == "RSS/Atom")
            self.assertEqual(rss_post["channel_username"], "RSS: The Daily Star")
            self.assertTrue(all(p["evidence_status"] == "UNVERIFIED" for p in payload["posts"]))
            self.assertEqual(payload["summary"]["configured_rss_sources"], 1)
            self.assertEqual(payload["summary"]["configured_channels"], 1)
            self.assertEqual(payload["summary"]["collection_errors"], 0)
            self.assertNotIn("analyst_decisions", payload)
            report_path = archive_dir / "2026-11-18" / "intelligence_report.json"
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report["report_version"], 12)
            self.assertEqual(report["hatewatch"]["hatewatch_version"], 2)
            self.assertEqual(report["hatewatch"]["unique_flagged_source_posts"], 0)
            self.assertEqual(report["triage_version"], 12)
            self.assertEqual(report["executive_assessment"]["relevant_source_posts"], 1)
            self.assertEqual(report["executive_assessment"]["excluded_as_low_relevance"], 1)
            self.assertEqual(report["executive_assessment"]["incident_candidate_source_posts"], 1)
            self.assertEqual(report["executive_assessment"]["bangladesh_relevant_source_posts"], 1)
            self.assertEqual(report["bangladesh_relevant_source_posts"], 1)
            bangladesh = next(section for section in report["report_sections"] if section["heading"].startswith("2."))
            self.assertEqual(bangladesh["bangladesh_relevant_posts"], 1)
            self.assertEqual(bangladesh["district_name_mentions"], {"Gazipur": 1})
            self.assertEqual(len(report["temporal_comparison"]), 8)
            region_section = next(section for section in report["report_sections"] if section["heading"].startswith("3."))
            self.assertEqual(len(region_section["regions"]), 9)
            self.assertTrue(region_section["all_regions_displayed"])
            audit = report["bangladesh_false_negative_audit"]
            self.assertEqual(audit["total_source_posts"], 2)
            self.assertEqual(audit["excluded_source_posts"], 1)
            self.assertEqual(audit["excluded_sample_count"], 1)
            candidate_section = next(section for section in report["report_sections"] if section["heading"].startswith("7."))
            candidate = candidate_section["candidate_records"][0]
            self.assertTrue(candidate["provisional_incident_id"].startswith("PL-2026-11-18-"))
            self.assertIn("unresolved single-source lead", candidate["incident_group_status"])

    def test_precision_triage_rejects_entertainment_and_generic_commentary(self):
        cases = [
            "Call of Duty game progression tips: attack and defend the objective.",
            "Open Eurasian Film Award ceremony held in Moscow.",
            "Minister uses Friday sermons to raise awareness against sabotage.",
            "Analyst discusses military strategy and missile range in a television interview.",
            "Third-party vendor reports a cybersecurity breach affecting customer data."
        ]
        for body in cases:
            with self.subTest(body=body):
                result = publish_tbc_feed.triage_source_post({"text": body})
                self.assertFalse(result["relevant"])
                self.assertFalse(result["incident_candidate"])

    def test_precision_triage_keeps_explicit_real_world_event_actions(self):
        cases = [
            ("Armed attack reported on a village; civilians injured.", "physical_incident_lead"),
            ("Workers blocked the road and clashed with police.", "civil_unrest_event_lead"),
            ("Police fired tear gas and dispersed protesters.", "civil_unrest_event_lead"),
            ("Security forces arrested opposition activists during a raid.", "security_action_lead")
        ]
        for body, expected_type in cases:
            with self.subTest(body=body):
                result = publish_tbc_feed.triage_source_post({"text": body})
                self.assertTrue(result["relevant"])
                self.assertTrue(result["incident_candidate"])
                self.assertEqual(result["record_type"], expected_type)

    def test_bangladesh_bengali_unrest_is_detected_for_review(self):
        body = "থানার সামনে বিক্ষোভকে কেন্দ্র করে আ’লীগ-বিএনপির ধাওয়া-পাল্টাধাওয়া"
        result = publish_tbc_feed.triage_source_post({"text": body})
        self.assertTrue(result["relevant"])
        self.assertTrue(result["incident_candidate"])
        self.assertIn("civil_unrest_claim", result["claim_types"])

    def test_political_commentary_is_not_a_physical_incident(self):
        for body in ["Trump weighs new strikes on Iran as peace talks stall; he is considering a new round of strikes.", "Tehran summit: Environment a silent victim of US-Israeli war on Iran; economist spoke at a seminar."]:
            with self.subTest(body=body):
                result = publish_tbc_feed.triage_source_post({"text": body})
                self.assertFalse(result["incident_candidate"])
                self.assertNotEqual(result["record_type"], "physical_incident_lead")

    def test_threat_is_not_a_completed_incident_candidate(self):
        result = publish_tbc_feed.triage_source_post({"text": "Group threatened to attack a government building."})
        self.assertTrue(result["relevant"])
        self.assertEqual(result["record_type"], "threat_or_mobilisation_lead")
        self.assertFalse(result["incident_candidate"])

    def test_multi_label_keeps_physical_event_and_preparation_claims(self):
        body = "Missile strike reported on the bridge; additional cruise missiles inbound."
        result = publish_tbc_feed.triage_source_post({"text": body})
        self.assertTrue(result["relevant"])
        self.assertTrue(result["incident_candidate"])
        self.assertIn("physical_incident_claim", result["claim_types"])
        self.assertIn("threat_or_preparation_claim", result["claim_types"])
        self.assertIn("missiles inbound", result["preparation_indicators"])

    def test_preparation_only_is_relevant_but_not_a_completed_incident(self):
        result = publish_tbc_feed.triage_source_post({
            "text": "Seven bombers ready for a possible launch; missile launch preparation reported."
        })
        self.assertTrue(result["relevant"])
        self.assertFalse(result["incident_candidate"])
        self.assertIn("threat_or_preparation_claim", result["claim_types"])
        self.assertEqual(result["record_type"], "threat_or_mobilisation_lead")

    def test_partial_current_day_is_not_comparison_eligible(self):
        from datetime import datetime
        from zoneinfo import ZoneInfo
        report_date = datetime.now(ZoneInfo("Asia/Dhaka")).date().isoformat()
        result = publish_tbc_feed.build_temporal_comparison(
            report_date,
            [{"text": "Armed attack reported on a village.", "priority_region": "bangladesh",
              "collected_at": report_date + "T03:00:00+00:00"}],
            Path("/nonexistent/archive"),
            "Asia/Dhaka"
        )
        self.assertEqual(result[0]["reporting_day_status"], "partial_day")
        self.assertFalse(result[0]["comparison_eligible"])
        self.assertIn("not directly comparable", result[0]["comparison_status"])

    def test_rejects_non_https_source_urls(self):
        row = {"channel_username":"bad", "message_id":"1", "text":"headline", "source_url":"http://example.org/a"}
        self.assertIsNone(publish_tbc_feed.normalize_row(row, "RSS/Atom"))


if __name__ == "__main__":
    unittest.main()
