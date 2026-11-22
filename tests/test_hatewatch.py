import unittest
from scripts.hatewatch import classify_post, build_hatewatch

class HatewatchV3Tests(unittest.TestCase):
    def test_english_attack_target_order_independent(self):
        result = classify_post({"text": "Police arrested suspects after a mob attacked Muslim families"})
        self.assertIn("hate_crime_incident", result["categories"])

    def test_bengali_bulldozer_demolition(self):
        result = classify_post({"text": "ভারতে এক মুসলিম পরিবারের বাড়ি বুলডোজারে গুঁড়িয়ে দিল"})
        self.assertIn("hate_crime_incident", result["categories"])
        self.assertIn("discrimination", result["categories"])

    def test_hindi_lynching(self):
        result = classify_post({"text": "मुस्लिम युवक की भीड़ ने पीट पीटकर हत्या की"})
        self.assertIn("hate_crime_incident", result["categories"])

    def test_urdu_torture(self):
        result = classify_post({"text": "مسلمان خاندان پر تشدد اور گھر سے بے دخل کرنے کا الزام"})
        self.assertIn("hate_crime_incident", result["categories"])
        self.assertIn("discrimination", result["categories"])

    def test_state_discrimination(self):
        result = classify_post({"text": "Muslim students barred from school under a new government order"})
        self.assertIn("discrimination", result["categories"])

    def test_bhagwa_love_trap_narrative(self):
        result = classify_post({"text": "Report examines the so-called Bhagwa love trap narrative and anti-Muslim propaganda"})
        self.assertIn("anti_muslim_propaganda", result["categories"])

    def test_bengali_propaganda(self):
        result = classify_post({"text": "মুসলিমবিরোধী বক্তব্য ও মুসলমানদের বয়কটের ডাক"})
        self.assertIn("anti_muslim_propaganda", result["categories"])

    def test_urdu_threat(self):
        result = classify_post({"text": "مسلمانوں کو دھمکی اور مسجد کو نشانہ بنانے کی بات"})
        self.assertIn("communal_tension", result["categories"])

    def test_islamic_revolutionary_guard_not_muslim_target(self):
        result = classify_post({"text": "Islamic Revolutionary Guard Corps attacked two US military bases in Bahrain"})
        self.assertNotIn("hate_crime_incident", result["categories"])
        self.assertFalse(result["relevant"])

    def test_islamic_state_and_boko_haram_not_muslim_target(self):
        result = classify_post({"text": "Islamic State West Africa fighters clashed with Boko Haram"})
        self.assertFalse(result["relevant"])

    def test_rohingya_identity_alone_not_enough(self):
        self.assertFalse(classify_post({"text": "Rohingya families discuss education and livelihoods"})["relevant"])

    def test_palestinian_conflict_not_automatically_hate_crime(self):
        self.assertFalse(classify_post({"text": "Airstrike killed Palestinian civilians in Gaza"})["relevant"])

    def test_historical_rohingya_testimony_separated(self):
        result = classify_post({"text": "Rohingya Muslim survivors recount 2017 killings, arson and sexual violence"})
        self.assertEqual(result["event_time_status"], "historical_or_retrospective")
        self.assertEqual(result["classification_status"], "historical_reference_review")

    def test_icj_historical_ruling_not_current_incident(self):
        result = classify_post({"text": "ICJ ruling on Myanmar: Rohingya refugees recall 2017 genocide"})
        self.assertEqual(result["event_time_status"], "historical_or_retrospective")

    def test_fact_check_is_context_review(self):
        result = classify_post({"text": "Fact check: false anti-Muslim claim used to incite violence against Muslim families"})
        self.assertIn("anti_muslim_propaganda", result["categories"])
        self.assertEqual(result["classification_status"], "context_review_required")

    def test_criticism_of_religion_not_hate(self):
        self.assertFalse(classify_post({"text": "A debate about Islamic theology and religious doctrine"})["relevant"])

    def test_exact_duplicate_posts_grouped_but_not_incidents(self):
        posts = [
            {"id":"a:1","text":"Attack on Muslim families reported","source_url":"https://example.org/a"},
            {"id":"b:2","text":"Attack on Muslim families reported","source_url":"https://example.org/b"},
        ]
        result = build_hatewatch(posts, lambda p: {"id":p["id"],"source_url":p["source_url"]})
        self.assertEqual(result["unique_flagged_source_posts"], 2)
        self.assertEqual(len(result["exact_duplicate_groups"]), 1)
        self.assertIsNone(result["unique_incident_count"])

    def test_counts_are_source_posts_and_overlaps_are_explicit(self):
        post = {"id":"x:1","text":"Attack on Muslim family; home demolished","source_url":"https://example.org/a"}
        result = build_hatewatch([post], lambda p: {"id":p["id"],"source_url":p["source_url"]})
        self.assertEqual(result["source_posts_screened"], 1)
        self.assertEqual(result["unique_flagged_source_posts"], 1)
        self.assertGreaterEqual(result["total_category_matches"], 1)
        self.assertEqual(result["categories"][0]["records"][0]["hatewatch"]["evidence_status"], "UNVERIFIED")

if __name__ == "__main__":
    unittest.main()
