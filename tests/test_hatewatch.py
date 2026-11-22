import unittest
from scripts.hatewatch import classify_post, build_hatewatch

class HatewatchV2Tests(unittest.TestCase):
    def test_english_attack_target_order_independent(self):
        result = classify_post({"text": "Police arrested suspects after a mob attacked Muslim families"})
        self.assertIn("hate_crime_incident", result["categories"])

    def test_bengali_mosque_attack(self):
        result = classify_post({"text": "মসজিদে হামলা ও মুসলমানদের বাড়িঘরে অগ্নিসংযোগের অভিযোগ"})
        self.assertIn("hate_crime_incident", result["categories"])

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

    def test_rohingya_identity_not_enough(self):
        result = classify_post({"text": "Rohingya families discuss education and livelihoods"})
        self.assertFalse(result["relevant"])

    def test_palestinian_conflict_not_automatically_hate_crime(self):
        result = classify_post({"text": "Airstrike killed Palestinian civilians in Gaza"})
        self.assertNotIn("hate_crime_incident", result["categories"])

    def test_fact_check_is_context_not_suppression(self):
        result = classify_post({"text": "Fact check: false anti-Muslim claim used to incite violence against Muslim families"})
        self.assertIn("anti_muslim_propaganda", result["categories"])
        self.assertEqual(result["classification_status"], "context_review_required")

    def test_criticism_of_religion_not_hate(self):
        self.assertFalse(classify_post({"text": "A debate about Islamic theology and religious doctrine"} )["relevant"])

    def test_build_records_unverified_and_screened_count(self):
        post = {"id": "x:1", "text": "Attack on Muslim families reported", "source_url": "https://example.org/a"}
        result = build_hatewatch([post], lambda item: {"id": item["id"], "source_url": item["source_url"]})
        self.assertEqual(result["unique_flagged_source_posts"], 1)
        self.assertEqual(result["source_posts_screened"], 1)
        self.assertEqual(result["categories"][0]["records"][0]["hatewatch"]["evidence_status"], "UNVERIFIED")

if __name__ == "__main__":
    unittest.main()
