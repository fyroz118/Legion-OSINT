import tempfile
import unittest
from pathlib import Path
from app import database, incidents
from app.report_builder import build_report_draft


class ReportDraftTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_path = database.DB_PATH
        database.DB_PATH = str(Path(self.temp_dir.name) / "report.sqlite3")
        database.initialize()
        incidents.initialize_incident_tables()

    def tearDown(self):
        database.DB_PATH = self.original_path
        self.temp_dir.cleanup()

    def test_empty_report_is_explicitly_a_draft(self):
        report = build_report_draft("2026-11-18")
        self.assertIn("DRAFT FROM INCIDENT LEDGER", report)
        self.assertIn("Empty sections are not evidence", report)
        self.assertIn("## Overall Intelligence Judgment", report)

    def test_incident_appears_in_register(self):
        incidents.upsert_incident({
            "incident_id": "BD-001", "report_date": "2026-11-18",
            "country": "Bangladesh", "category": "civil_unrest",
            "description": "A demonstration reported by a public source."
        })
        report = build_report_draft("2026-11-18")
        self.assertIn("A demonstration reported by a public source.", report)
        self.assertIn("Bangladesh", report)

    def test_report_discloses_review_state_and_analyst_source_classes(self):
        from app.research import run_research, review_lead, get_research_leads
        def fake_search(query, report_date, max_results=10):
            return {"results": [{
                "title": "Independent report on a public event",
                "url": "https://independent.example.org/event",
                "content": "A report requiring corroboration.",
                "published_date": report_date,
            }]}
        run_research("2026-11-18", max_queries=1, search_fn=fake_search)
        lead_id = get_research_leads("2026-11-18")[0]["id"]
        review_lead(lead_id, "REVIEWED", source_class="independent_media")
        report = build_report_draft("2026-11-18")
        self.assertIn("Analyst review status: REVIEWED: 1", report)
        self.assertIn("independent_media: 1", report)

if __name__ == "__main__":
    unittest.main()
