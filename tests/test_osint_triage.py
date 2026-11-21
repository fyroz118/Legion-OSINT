import json
import tempfile
import unittest
from pathlib import Path
from scripts import publish_tbc_feed
from scripts.publish_tbc_feed import triage_source_post, district_mentions, build_repost_clusters


class OsintTriageTests(unittest.TestCase):
    def test_unrelated_celebrity_post_is_filtered(self):
        item = {"text": "Actress wears a bridal dress in a fashion photo shoot."}
        self.assertFalse(triage_source_post(item)["relevant"])

    def test_conflict_lead_is_retained_as_unverified_candidate(self):
        item = {"text": "Local media report an armed attack and three people were injured."}
        triage = triage_source_post(item)
        self.assertTrue(triage["relevant"])
        self.assertTrue(triage["incident_candidate"])

    def test_labour_unrest_is_relevant(self):
        item = {"text": "Workers began a protest and blockade over unpaid wages."}
        self.assertTrue(triage_source_post(item)["relevant"])

    def test_district_mentions_are_text_only(self):
        self.assertEqual(district_mentions("Reports from Gazipur and Narayanganj"), ["Gazipur", "Narayanganj"])

    def test_same_publisher_repetition_is_not_cross_source(self):
        posts = [
            {"text": "A sufficiently long repeated source statement " * 5, "publisher_name": "Channel A", "platform": "Telegram", "source_url": "https://t.me/a/1"},
            {"text": "A sufficiently long repeated source statement " * 5, "publisher_name": "Channel A", "platform": "Telegram", "source_url": "https://t.me/a/2"}
        ]
        clusters = build_repost_clusters(posts, lambda item: item)
        self.assertEqual(len(clusters), 1)
        self.assertEqual(clusters[0]["distinct_source_count"], 1)
        self.assertEqual(clusters[0]["repetition_type"], "same-source repetition")

    def test_cross_source_repetition_is_flagged_not_verified(self):
        text = "A sufficiently long repeated source statement " * 5
        posts = [
            {"text": text, "publisher_name": "Channel A", "platform": "Telegram"},
            {"text": text, "publisher_name": "Channel B", "platform": "Telegram"}
        ]
        clusters = build_repost_clusters(posts, lambda item: item)
        self.assertEqual(clusters[0]["distinct_source_count"], 2)
        self.assertIn("independence unassessed", clusters[0]["repetition_type"])

    def test_substring_war_match_does_not_flag_award(self):
        item = {"text": "The award ceremony attracted international filmmakers."}
        self.assertFalse(triage_source_post(item)["relevant"])

    def test_protest_announcement_is_not_a_completed_incident(self):
        item = {"text": "The party announced protest programmes for next month."}
        triage = triage_source_post(item)
        self.assertTrue(triage["relevant"])
        self.assertFalse(triage["incident_candidate"])
        self.assertEqual(triage["record_type"], "protest_or_mobilisation_notice")

    def test_actual_unrest_action_is_a_candidate(self):
        item = {"text": "Workers staged a protest and police fired tear gas."}
        triage = triage_source_post(item)
        self.assertTrue(triage["incident_candidate"])
        self.assertEqual(triage["record_type"], "civil_unrest_event_lead")

    def test_threat_is_not_mislabelled_as_completed_attack(self):
        item = {"text": "The group threatened an attack on the facility."}
        triage = triage_source_post(item)
        self.assertTrue(triage["relevant"])
        self.assertFalse(triage["incident_candidate"])
        self.assertEqual(triage["record_type"], "threat_or_mobilisation_lead")

    def test_exact_candidate_groups_retain_source_posts(self):
        text = "A sufficiently detailed armed attack was reported near the central bridge, with several people injured. "
        posts = [
            {"text": text, "publisher_name": "Outlet A", "platform": "Telegram"},
            {"text": text, "publisher_name": "Outlet B", "platform": "RSS/Atom"}
        ]
        groups = publish_tbc_feed.build_candidate_groups(posts, lambda item: item)
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["source_post_count"], 2)
        self.assertEqual(groups[0]["distinct_source_count"], 2)
        self.assertIn("not corroboration", groups[0]["independence_assessment"])

    def test_temporal_comparison_uses_dates_and_distinguishes_empty_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp)
            (archive / "2026-11-18.json").write_text(json.dumps({"posts": []}), encoding="utf-8")
            rows = publish_tbc_feed.build_temporal_comparison("2026-11-19", [], archive)
            self.assertEqual(rows[0]["date"], "2026-11-19")
            self.assertEqual(rows[1]["date"], "2026-11-18")
            self.assertEqual(rows[1]["comparison_status"], "archive available; collection completeness unverified")
            self.assertEqual(rows[1]["collected_posts"], 0)


if __name__ == "__main__":
    unittest.main()
