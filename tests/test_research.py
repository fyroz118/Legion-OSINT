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

    def test_query_plan_prioritizes_bangladesh_and_is_date_scoped(self):
        plan = build_query_plan("2026-11-18")
        self.assertEqual(plan[0]["region"], "Bangladesh")
        self.assertEqual(plan[0]["report_date"], "2026-11-18")
        self.assertEqual(len(plan), 12)

    def test_invalid_date_rejected(self):
        with self.assertRaises(ValueError):
            build_query_plan("18-11-2026")

    def test_search_results_are_saved_as_leads(self):
        def fake_search(query, report_date, max_results=5):
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
        self.assertEqual(sum(x["query_count"] for x in get_research_coverage("2026-11-18")), 2)


    def test_known_out_of_window_publications_are_filtered(self):
        def fake_search(query, report_date, max_results=5):
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
        def fail_search(query, report_date, max_results=5):
            raise RuntimeError("provider unavailable")
        summary = run_research("2026-11-18", max_queries=1, search_fn=fail_search)
        self.assertEqual(summary["queries_succeeded"], 0)
        self.assertEqual(len(summary["errors"]), 1)
        self.assertEqual(get_research_coverage("2026-11-18")[0]["status"], "failed")


if __name__ == "__main__":
    unittest.main()
