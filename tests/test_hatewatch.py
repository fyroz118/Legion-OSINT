import unittest
from scripts.hatewatch import classify_post, build_hatewatch

class HatewatchTests(unittest.TestCase):
 def test_bengali_incident(self):
  self.assertIn("hate_crime_incident",classify_post({"text":"মসজিদে হামলা ও ভাঙচুরের অভিযোগ"})["categories"])
 def test_hindi_propaganda(self):
  self.assertIn("anti_muslim_propaganda",classify_post({"text":"मुसलमानों को देश से निकालो"})["categories"])
 def test_urdu_tension(self):
  self.assertIn("communal_tension",classify_post({"text":"مسلمانوں کے خلاف دھمکی"})["categories"])
 def test_religion_criticism_not_flagged(self):
  self.assertFalse(classify_post({"text":"A debate about religious doctrine and theology"})["relevant"])
 def test_fact_check_context(self):
  self.assertNotIn("anti_muslim_propaganda",classify_post({"text":"Fact check: false claim used in anti-muslim propaganda"})["categories"])
 def test_build_records_are_unverified(self):
  p={"id":"x:1","text":"Attack on Muslims reported","source_url":"https://example.org/a"}
  out=build_hatewatch([p],lambda x:{"id":x["id"]})
  self.assertEqual(out["unique_flagged_source_posts"],1)
  self.assertEqual(out["categories"][0]["records"][0]["hatewatch"]["evidence_status"],"UNVERIFIED")
if __name__ == "__main__": unittest.main()
