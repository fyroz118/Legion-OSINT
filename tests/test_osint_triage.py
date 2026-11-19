import unittest
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


if __name__ == "__main__":
    unittest.main()
