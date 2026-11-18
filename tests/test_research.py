import tempfile
import unittest
from pathlib import Path
from app import database
from app.research import build_query_plan, run_research, get_research_leads, get_research_coverage


class ResearchTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_path = database.DB_PATH
        database.DB_PATH = str(Path(self.temp_dir.name) / "research.sqlite3")
        database.initialize()

    def tearDown(self):
        database.DB_PATH = self.original_path
        self.temp_dir.cleanup()

    def test_default_plan_has_60_queries_and_prioritizes_bangladesh(self):
        plan = build_query_plan("2026-11-18")
        self.assertEqual(len(plan), 60)
        self.assertEqual(plan[0]["region"], "Bangladesh")
        self.assertEqual(plan[0]["report_date"], "2026-11-18")
        self.assertEqual(sum(x["source_focus"] == "unofficial_public" for x in plan), 42)
        self.assertEqual(sum(x["source_focus"] == "official_institutional" for x in plan), 18)

    def test_plan_includes_rumour_discovery_and_geographic_priorities(self):
        plan = build_query_plan("2026-11-18")
        self.assertTrue(any(x["claim_type"] == "RUMOUR_WATCH" for x in plan))
        regions = {x["region"] for x in plan}
        self.assertIn("Bangladesh", regions)
        self.assertIn("South Asia", regions)
        self.assertIn("Middle East and North Africa", regions)
        self.assertIn("Americas", regions)

    def test_query_limit_is_capped(self):
        self.assertEqual(len(build_query_plan("2026-11-18", max_queries=200)), 100)

    def test_invalid_date_rejected(self):
        with self.assertRaises(ValueError):
            build_query_plan("18-11-2026")

    def test_search_results_are_saved_as_unreviewed_leads(self):
        def fake_search(query, report_date, max_results=10):
            return {"results": [{
                "title": "Public report", "url": "https://news.example.org/story",
                "content": "A public report requiring corroboration.",
                "published_date": report_date, "score": 0.87,
            }]}
        summary = run_research("2026-11-18", max_queries=2, search_fn=fake_search)
        self.assertEqual(summary["queries_succeeded"], 2)
        self.assertEqual(summary["leads_saved"], 2)
        leads = get_research_leads("2026-11-18")
        self.assertEqual(len(leads), 1)
        self.assertEqual(leads[0]["region"], "Bangladesh")
        self.assertEqual(leads[0]["review_status"], "UNREVIEWED")
        self.assertEqual(sum(x["query_count"] for x in get_research_coverage("2026-11-18")), 2)

    def test_known_out_of_window_publications_are_filtered(self):
        def fake_search(query, report_date, max_results=10):
            return {"results": [
                {"title": "In-window", "url": "https://news.example.org/in", "published_date": "2026-11-18T12:00:00Z"},
                {"title": "Out-of-window", "url": "https://news.example.org/out", "published_date": "2026-11-17T16:00:00Z"},
                {"title": "Undated", "url": "https://news.example.org/unknown"},
            ]}
        run_research("2026-11-18", max_queries=1, search_fn=fake_search)
        leads = get_research_leads("2026-11-18")
        self.assertEqual({x["source_url"] for x in leads}, {
            "https://news.example.org/in", "https://news.example.org/unknown"
        })

    def test_failed_provider_call_is_recorded_not_hidden(self):
        def fail_search(query, report_date, max_results=10):
            raise RuntimeError("provider unavailable")
        summary = run_research("2026-11-18", max_queries=1, search_fn=fail_search)
        self.assertEqual(summary["queries_succeeded"], 0)
        self.assertEqual(len(summary["errors"]), 1)
        self.assertEqual(get_research_coverage("2026-11-18")[0]["status"], "failed")


    def test_review_workflow_requires_explicit_classification_and_existing_incident(self):
        from app.research import review_queue, review_lead, link_reviewed_lead_to_incident
        def fake_search(query, report_date, max_results=10):
            return {"results": [{
                "title": "A distinct public incident report title",
                "url": "https://review.example.org/story",
                "content": "A claim that requires corroboration.",
                "published_date": report_date,
            }]}
        run_research("2026-11-18", max_queries=1, search_fn=fake_search)
        lead = review_queue("2026-11-18")[0]
        with self.assertRaises(ValueError):
            link_reviewed_lead_to_incident(lead["id"], "missing-incident")
        from app.incidents import upsert_incident
        upsert_incident({
            "incident_id": "BD-REVIEW-001", "report_date": "2026-11-18",
            "country": "Bangladesh", "category": "civil_unrest",
            "description": "Analyst-created incident record pending verification."
        })
        review_lead(lead["id"], "REVIEWED", source_class="independent_media")
        self.assertTrue(link_reviewed_lead_to_incident(lead["id"], "BD-REVIEW-001"))
        from app.incidents import get_report_incidents
        self.assertEqual(len(get_report_incidents("2026-11-18")[0]["sources"]), 1)

    def test_duplicate_decision_requires_existing_other_lead(self):
        from app.research import review_lead
        def fake_search(query, report_date, max_results=10):
            return {"results": [{
                "title": "Same result", "url": "https://duplicate.example.org/story",
                "published_date": report_date,
            }]}
        run_research("2026-11-18", max_queries=1, search_fn=fake_search)
        lead_id = get_research_leads("2026-11-18")[0]["id"]
        with self.assertRaises(ValueError):
            review_lead(lead_id, "DUPLICATE")


    def test_candidate_extraction_does_not_invent_incident_fields(self):
        from app.research import extract_event_candidates
        def fake_search(query, report_date, max_results=10):
            return {"results": [{
                "title": "Demonstrators gather outside district office",
                "url": "https://candidate.example.org/report",
                "content": "A local outlet reports a gathering; details remain unclear.",
                "published_date": report_date,
            }]}
        run_research("2026-11-18", max_queries=1, search_fn=fake_search)
        candidate = extract_event_candidates("2026-11-18")[0]
        self.assertEqual(candidate["candidate_status"], "UNVERIFIED_CANDIDATE")
        self.assertEqual(candidate["verification_status"], "UNVERIFIED")
        self.assertIsNone(candidate["incident_date"])
        self.assertIsNone(candidate["location"])
        self.assertIsNone(candidate["actors"])
        self.assertEqual(candidate["source_url"], "https://candidate.example.org/report")

    def test_duplicate_suggestions_never_merge_leads(self):
        from app.research import suggest_duplicate_candidates, get_research_leads
        def fake_search(query, report_date, max_results=10):
            return {"results": [
                {"title": "Protesters gather outside district office today", "url": "https://a.example.org/story", "published_date": report_date},
                {"title": "Protesters gather outside district office today update", "url": "https://b.example.org/story", "published_date": report_date},
            ]}
        run_research("2026-11-18", max_queries=1, search_fn=fake_search)
        before = len(get_research_leads("2026-11-18"))
        suggestions = suggest_duplicate_candidates("2026-11-18")
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0]["decision"], "HUMAN_REVIEW_REQUIRED")
        self.assertEqual(len(get_research_leads("2026-11-18")), before)


if __name__ == "__main__":
    unittest.main()
